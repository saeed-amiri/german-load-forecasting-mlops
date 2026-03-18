# configs/config_runtime.py
"""
Setting up configuration for runtime paths
It will be handle by configs/main.py
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    """Derived runtime paths that are independent from YAML content."""

    project_root: Path
    config_file: Path
    logs_dir: Path
    sql_dir: Path


def initialize_runtime_paths(project_root, config_path, sql) -> RuntimePaths:
    runtime = RuntimePaths(
        project_root=project_root,
        config_file=config_path.resolve(),
        logs_dir=(project_root / "logs").resolve(),
        sql_dir=(project_root / sql.root).resolve(),
    )

    return runtime
