# configs/config_utils.py
"""
Helper functions for the config
It will be handled by configs/main.py
"""

import logging
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader


def render_config_file(config_path: Path) -> dict:
    """Read the config file and handle the input ingestion with ninja"""
    input_dir: Path = config_path.parent / "inputs"
    context = {}
    for name in ["sql", "api", "paths", "logging"]:
        file_path = input_dir / f"{name}.yml"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing expected config input: {file_path}")
        context[name] = yaml.safe_load(file_path.read_text())

    env = Environment(loader=FileSystemLoader(config_path.parent))
    template = env.get_template(config_path.name)
    rendered = template.render(**context)

    try:
        return yaml.safe_load(rendered) or {}
    except yaml.YAMLError as err:
        raise RuntimeError("Failed to parse rendered YAML from %s", config_path) from err


def discover_project_root(start_path: Path | None = None) -> Path:
    """Find project root by walking up until standard project markers are found."""
    anchor = (start_path or Path.cwd()).resolve()
    if anchor.is_file():
        anchor = anchor.parent

    for candidate in [anchor, *anchor.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "configs").is_dir():
            return candidate

    raise FileNotFoundError(f"Unable to locate project root from '{anchor}'. Expected 'pyproject.toml' and 'configs/'.")


def resolve_config_path(project_root: Path, config_name: str) -> Path:
    config_dir = project_root / "configs"
    explicit = config_dir / config_name

    if explicit.suffix in {".yml", ".yaml"}:
        if explicit.exists():
            return explicit
        raise FileNotFoundError(f"Configuration file not found at {explicit}")

    for suffix in (".yml", ".yaml"):
        candidate = config_dir / f"{config_name}{suffix}"
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Configuration file '{config_name}' not found under {config_dir} (.yml/.yaml).")


def initialize_project_root(
    config_name: str, project_root: Path | None, start_file: Path | None, logger: logging.Logger
) -> tuple[Path, Path]:
    if project_root is None:
        project_root = discover_project_root(start_path=start_file)
    else:
        project_root = project_root.resolve()
    logger.info(f"The project root is: >> {project_root} <<")

    config_path = resolve_config_path(project_root=project_root, config_name=config_name)
    return project_root, config_path
