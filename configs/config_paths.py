# configs/config_paths.py
"""
Setting up configuration for paths
It will be handled by configs/main.py
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class PathSettings(BaseModel):
    """Internal file system locations."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    processed_file: Path = Field(alias="processed_data")
    database: Path
    marts_dir: Path = Field(alias="marts_data_dir")
    models_dir: Path = Field(alias="models_dir")
