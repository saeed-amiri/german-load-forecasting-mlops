# core/config.py
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
class SQLConfig:
    """Internal parameters of handling SQL"""
    chunk_size: int = 5000
    table_name: str = "german_load_clean"
    transform: str = "transform.sql"


@dataclass(frozen=True)
class PipelineConfig:
    """
    Master configuration for the data processing lifecycle.
    """

    paths: PathSettings
    sql: SQLConfig

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
            raw_file=(project_root / config_dict["paths"]["raw_data"]).resolve(),
            processed_file=(project_root / config_dict["paths"]["processed_data"]).resolve(),
            database=(project_root / config_dict["paths"]["database"]).resolve(),
        )

        try:
            sql = SQLConfig(
                chunk_size=int(config_dict["sql"]["chunk_size"]),
                table_name=config_dict["sql"]["table_name"],
                transform=config_dict["sql"]["transform"],
            )
        except (KeyError, ValueError, TypeError):
            logger.warning("Problems in reading SQL parameters, rolls back to the default values")
            sql = SQLConfig()

        logger.info(f"Configuration loaded successfully from {config_path}")

        return cls(paths=paths, sql=sql)
