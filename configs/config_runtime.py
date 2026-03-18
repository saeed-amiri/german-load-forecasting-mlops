# configs/config_runtime.py
"""
Setting up configuration for runtime paths
It will be handled by configs/main.py
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class RuntimePaths(BaseModel):
    """Derived runtime paths that are independent from YAML content."""

    model_config = ConfigDict(frozen=True)

    project_root: Path
    config_file: Path
    logs_dir: Path
    sql_dir: Path
