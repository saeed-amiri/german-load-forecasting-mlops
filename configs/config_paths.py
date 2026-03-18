# configs/config_paths.py
"""
Setting up configuration for paths
It will be handle by configs/main.py
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathSettings:
    """Internal file system locations."""

    raw_file: Path
    processed_file: Path
    database: Path


def initialize_path_settings(project_root, path_config) -> PathSettings:
    paths = PathSettings(
        raw_file=(project_root / path_config["raw_data"]).resolve(),
        processed_file=(project_root / path_config["processed_data"]).resolve(),
        database=(project_root / path_config["database"]).resolve(),
    )

    return paths
