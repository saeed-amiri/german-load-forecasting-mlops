# configs/main.py
"""
Setting up the configurations for the pipeline
"""

import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .config_api import APIConfig, initialize_api_config
from .config_logs import LoggingConfig, initialize_logging_config
from .config_paths import PathSettings, initialize_path_settings
from .config_runtime import RuntimePaths, initialize_runtime_paths
from .config_sql import SQLConfig, initialize_sql_config
from .config_utils import initialize_project_root, parse_yaml_file

logger = logging.getLogger(__name__)


class PipelineConfig(BaseModel):
    """
    Data-only application configuration container.
    """

    model_config = ConfigDict(frozen=True)

    project_root: Path
    paths: PathSettings
    sql: SQLConfig
    runtime: RuntimePaths
    logging: LoggingConfig
    api: APIConfig


def load_config(
    config_name: str = "config",
    project_root: Path | None = None,
    start_file: Path | None = None,
) -> PipelineConfig:
    """Load and compose all config sections into a single immutable object."""

    project_root, config_path = initialize_project_root(config_name, project_root, start_file, logger)

    config_dict = parse_yaml_file(config_path, logger)

    path_config = config_dict.get("paths", {})
    if not path_config:
        raise KeyError("Missing required 'paths' section in config.")

    paths = initialize_path_settings(project_root, path_config)
    sql = initialize_sql_config(config_dict, logger)
    log_cfg = initialize_logging_config(config_dict)
    runtime = initialize_runtime_paths(project_root, config_path, sql)
    api = initialize_api_config(project_root, config_dict)

    logger.info("Configuration loaded successfully from %s", config_path)

    return PipelineConfig(
        project_root=project_root,
        paths=paths,
        sql=sql,
        runtime=runtime,
        logging=log_cfg,
        api=api,
    )
