# configs/config_paths.py
"""
Setting up configuration for paths
It will be handled by configs/main.py
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class PathSettings(BaseModel):
    """Internal file system locations."""

    model_config = ConfigDict(frozen=True)

    raw_file: Path
    processed_file: Path
    database: Path


def initialize_path_settings(project_root: Path, path_config: dict[str, str]) -> PathSettings:
    paths = PathSettings(
        raw_file=(project_root / path_config["raw_data"]).resolve(),
        processed_file=(project_root / path_config["processed_data"]).resolve(),
        database=(project_root / path_config["database"]).resolve(),
    )

    return paths
