# configs/main.py
"""
Setting up the configurations for the pipeline
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from core.log_utils import setup_logging

from .config_api import APIConfig, initialize_api_config
from .config_logs import LoggingConfig, initialize_logging_config
from .config_paths import PathSettings, initialize_path_settings
from .config_runtime import RuntimePaths, initialize_runtime_paths
from .config_sql import SQLConfig, initialize_sql_config, sql_script_path
from .config_utils import initialize_project_root, parse_yaml_file

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineConfig:
    """
    Master configuration for the data processing lifecycle.
    """

    project_root: Path
    paths: PathSettings
    sql: SQLConfig
    runtime: RuntimePaths
    logging: LoggingConfig
    api: APIConfig

    @classmethod
    def load(
        cls,
        config_name: str = "config",
        project_root: Path | None = None,
        start_file: Path | None = None,
    ) -> PipelineConfig:
        """
        Initializes the full project configuration by resolving paths and loading YAML settings.

        This method acts as a factory that orchestrates the discovery of the project root,
        resolution of the configuration file, and the construction of validated
        Path, SQL, and Logging settings.

        Args:
            config_name: The name of the YAML file (with or without .yml extension).
            project_root: Optional explicit path to the project root. If None,
                it is automatically discovered using project markers.
            start_file: Optional path to start the root discovery search from.
                Defaults to the current working directory.

        Returns:
            An initialized and validated PipelineConfig instance.

        Raises:
            FileNotFoundError: If the project root cannot be located or the
                specified configuration file is missing.
            KeyError: If the YAML file is missing the required 'paths' section.
            yaml.YAMLError: If the configuration file contains invalid syntax.
        """

        project_root, config_path = initialize_project_root(config_name, project_root, start_file, logger)

        config_dict = parse_yaml_file(config_path, logger)

        path_config = config_dict.get("paths", {})
        if not path_config:
            raise KeyError("Missing required 'paths' section in config.")

        # Path Settings (Using the same 'config_dict' everywhere)
        paths = initialize_path_settings(project_root, path_config)

        sql = initialize_sql_config(config_dict, logger)

        log_cfg = initialize_logging_config(config_dict)

        runtime = initialize_runtime_paths(project_root, config_path, sql)

        api = initialize_api_config(project_root, config_dict)

        logger.info(f"Configuration loaded successfully from {config_path}")

        return cls(project_root=project_root, paths=paths, sql=sql, runtime=runtime, logging=log_cfg, api=api)

    def service_log_path(self, service_name: str) -> Path:
        """Resolve per-service log file path using configured naming rules."""
        service_key = service_name.lower()
        service_map = {
            "ingestion": self.logging.ingestion_log,
            "preprocessing": self.logging.preprocessing_log,
        }
        log_name = service_map.get(service_key, f"{service_key}.log")
        return self.runtime.logs_dir / log_name

    def setup_service_logging(
        self,
        service_name: str,
        level: int | None = None,
        to_console: bool | None = None,
    ) -> Path:
        """Configure logging for a service based on centralized config."""
        log_path = self.service_log_path(service_name)
        setup_logging(
            log_file=log_path,
            level=level if level is not None else self.logging.level,
            to_consle=self.logging.to_console if to_console is None else to_console,
        )
        return log_path

    def transformation_sql_path(self) -> Path:
        return sql_script_path(self.sql.entrypoints.data.ingestion.transform, self.runtime.sql_dir)

    def quality_check_sql_path(self) -> Path:
        return sql_script_path(self.sql.entrypoints.data.preprocessing.quality_check, self.runtime.sql_dir)

    def api_target_view_sql_path(self) -> Path:
        return sql_script_path(self.sql.entrypoints.api.target_view, self.runtime.sql_dir)
