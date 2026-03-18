# configs/config_runtime.py
"""
Setting up configuration for runtime paths
It will be handled by configs/main.py
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .config_sql import SQLConfig


class RuntimePaths(BaseModel):
    """Derived runtime paths that are independent from YAML content."""

    model_config = ConfigDict(frozen=True)

    project_root: Path
    config_file: Path
    logs_dir: Path
    sql_dir: Path


def initialize_runtime_paths(project_root: Path, config_path: Path, sql: SQLConfig) -> RuntimePaths:
    runtime = RuntimePaths(
        project_root=project_root,
        config_file=config_path.resolve(),
        logs_dir=(project_root / "logs").resolve(),
        sql_dir=(project_root / sql.root).resolve(),
    )

    return runtime
