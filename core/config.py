"""
Setting up the configurations for the pipeline
"""

import logging
import yaml
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PathSettings:
    """Internal file system locations."""

    raw_file: Path
    processed_file: Path
    database: Path


@dataclass(frozen=True)
class PipelineConfig:
    """
    Master configuration for the data processing lifecycle.
    """

    paths: PathSettings

    @classmethod
    def load(cls, config_name: str, project_root: Path) -> PipelineConfig:
        """
        function to load YAML and return a structured PipelineConfig.
        """
        config_path = project_root / "configs" / f"{config_name}.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file '{config_name}' not found at {config_path}")

        with open(config_path, "r", encoding="utf8") as f:
            try:
                # We use 'config_dict' to be crystal clear
                config_dict = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                logger.error("Failed to parse YAML at %s", config_path, exc_info=True)
                raise exc

        # Path Settings (Using the same 'config_dict' everywhere)
        paths = PathSettings(
            raw_file=project_root / config_dict["paths"]["raw_data"],
            processed_file=project_root / config_dict["paths"]["processed_data"],
            database=project_root / config_dict["paths"]["database"],
        )

        logger.info(f"Configuration loaded successfully from {config_path}")

        return cls(paths=paths)
    