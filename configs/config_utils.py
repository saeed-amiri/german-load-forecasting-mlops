# configs/config_utils.py
"""
Helper functions for the config
It will be handle by configs/main.py
"""

import logging
from pathlib import Path
from typing import Any

import yaml


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


def parse_yaml_file(config_path: Path, logger: logging.Logger) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf8") as f:
        try:
            config_dict = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            logger.error("Failed to parse YAML at %s", config_path, exc_info=True)
            raise exc
    return config_dict
