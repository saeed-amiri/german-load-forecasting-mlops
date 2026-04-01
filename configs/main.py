# configs/main.py
"""
Setting up the configurations for the pipeline
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config_api import APIConfig
from .config_auth import AuthConfig
from .config_logs import LoggingConfig
from .config_paths import PathSettings
from .config_runtime import RuntimePaths
from .config_sql import SQLConfig
from .config_utils import initialize_project_root, render_config_file

logger = logging.getLogger(__name__)


class PipelineConfig(BaseModel):
    """
    Data-only application configuration container.
    """

    model_config = ConfigDict(frozen=True)

    project_root: Path
    config_file: Path = Field(repr=False, exclude=True)
    paths: PathSettings
    sql: SQLConfig
    logging: LoggingConfig
    api: APIConfig
    auth: AuthConfig
    runtime: Optional[RuntimePaths] = Field(default=None)

    @staticmethod
    def _to_abs(base: Path, value: Path) -> Path:
        return value.resolve() if value.is_absolute() else (base / value).resolve()

    @model_validator(mode="after")
    def resolve_paths_and_runtime(self) -> PipelineConfig:
        resolved_paths = self.paths.model_copy(
            update={
                "processed_file": self._to_abs(self.project_root, self.paths.processed_file),
                "database": self._to_abs(self.project_root, self.paths.database),
                "marts_dir": self._to_abs(self.project_root, self.paths.marts_dir),
            }
        )

        resolved_api = self.api.model_copy(
            update={
                "templates": self._to_abs(self.project_root, self.api.templates),
                "static": self._to_abs(self.project_root, self.api.static),
            }
        )

        resolved_auth = self.auth.model_copy(
            update={
                "database": self._to_abs(self.project_root, self.auth.database),
                "init_sql": self._to_abs(self.project_root, self.auth.init_sql),
            }
        )

        runtime = RuntimePaths(
            project_root=self.project_root,
            config_file=self.config_file.resolve(),
            logs_dir=(self.project_root / "logs").resolve(),
            sql_dir=(self.project_root / self.sql.root).resolve(),
        )

        return self.model_copy(
            update={
                "paths": resolved_paths,
                "api": resolved_api,
                "auth": resolved_auth,
                "runtime": runtime,
            }
        )


def load_config(
    config_name: str = "config",
    project_root: Path | None = None,
    start_file: Path | None = None,
) -> PipelineConfig:
    """Load and validate YAML configuration into a typed immutable model."""

    project_root, config_path = initialize_project_root(config_name, project_root, start_file, logger)

    config_dict = render_config_file(config_path)

    config_dict["project_root"] = project_root
    config_dict["config_file"] = config_path

    try:
        config = PipelineConfig.model_validate(config_dict)
    except Exception as exc:
        logger.error("Configuration validation failed: %s", exc)
        raise

    logger.info("Configuration loaded successfully from %s", config_path)
    return config
