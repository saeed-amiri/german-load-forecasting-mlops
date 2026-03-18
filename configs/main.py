# configs/main.py
"""
Setting up the configurations for the pipeline
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from core.log_utils import setup_logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PathSettings:
    """Internal file system locations."""

    raw_file: Path
    processed_file: Path
    database: Path


@dataclass(frozen=True)
class RuntimePaths:
    """Derived runtime paths that are independent from YAML content."""

    project_root: Path
    config_file: Path
    logs_dir: Path
    sql_dir: Path


@dataclass(frozen=True)
class LoggingConfig:
    """Logging behavior and file naming for services."""

    level: int = logging.INFO
    to_console: bool = True
    ingestion_log: str = "ingest.log"
    preprocessing_log: str = "preprocess.log"


@dataclass(frozen=True)
class SQLTables:
    """Maps to sql.tables in config.yml."""

    target: str = "german_load_clean"


@dataclass(frozen=True)
class SQLIngestionEntrypoints:
    """Maps to sql.entrypoints.data.ingestion."""

    transform: str = "00_transform.sql"


@dataclass(frozen=True)
class SQLPreprocessingEntrypoints:
    """Maps to sql.entrypoints.data.preprocessing."""

    quality_check: str = "quality_check.sql"


@dataclass(frozen=True)
class SQLDataEntrypoints:
    """Maps to sql.entrypoints.data."""

    ingestion: SQLIngestionEntrypoints = field(default_factory=SQLIngestionEntrypoints)
    preprocessing: SQLPreprocessingEntrypoints = field(default_factory=SQLPreprocessingEntrypoints)


@dataclass(frozen=True)
class SQLApiEntrypoints:
    """Maps to sql.entrypoints.api."""

    target_view: str = "target_view.sql"


@dataclass(frozen=True)
class SQLEntrypoints:
    """Maps to sql.entrypoints."""

    data: SQLDataEntrypoints = field(default_factory=SQLDataEntrypoints)
    api: SQLApiEntrypoints = field(default_factory=SQLApiEntrypoints)


@dataclass(frozen=True)
class SQLConfig:
    """Maps to the sql section of config.yml exactly."""

    root: str = "sql"
    chunk_size: int = 5000
    tables: SQLTables = field(default_factory=SQLTables)
    entrypoints: SQLEntrypoints = field(default_factory=SQLEntrypoints)


@dataclass(frozen=True)
class APIConfig:
    """Settings and parameters for API"""

    templates: Path


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
    def _discover_project_root(cls, start_path: Path | None = None) -> Path:
        """Find project root by walking up until standard project markers are found."""
        anchor = (start_path or Path.cwd()).resolve()
        if anchor.is_file():
            anchor = anchor.parent

        for candidate in [anchor, *anchor.parents]:
            if (candidate / "pyproject.toml").exists() and (candidate / "configs").is_dir():
                return candidate

        raise FileNotFoundError(
            f"Unable to locate project root from '{anchor}'. Expected 'pyproject.toml' and 'configs/'."
        )

    @classmethod
    def _resolve_config_path(cls, project_root: Path, config_name: str) -> Path:
        config_dir = project_root / "configs"
        explicit = config_dir / config_name

        if explicit.suffix in {".yml", ".yaml"}:
            if explicit.exists():
                return explicit
            raise FileNotFoundError(f"Configuration file not found at {explicit}")

        for suffix in (".yml", ".yaml"):
            candidate = config_dir / f"{config_name}{suffix}"
            if candidate.exists():
                return candidate

        raise FileNotFoundError(f"Configuration file '{config_name}' not found under {config_dir} (.yml/.yaml).")

    @staticmethod
    def _parse_log_level(raw_level: Any) -> int:
        if isinstance(raw_level, int):
            return raw_level
        if isinstance(raw_level, str):
            return getattr(logging, raw_level.upper(), logging.INFO)
        return logging.INFO

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

        if project_root is None:
            project_root = cls._discover_project_root(start_path=start_file)
        else:
            project_root = project_root.resolve()
        logger.info(f"The project root is: >> {project_root} <<")

        config_path = cls._resolve_config_path(project_root=project_root, config_name=config_name)

        with open(config_path, "r", encoding="utf8") as f:
            try:
                config_dict = yaml.safe_load(f) or {}
            except yaml.YAMLError as exc:
                logger.error("Failed to parse YAML at %s", config_path, exc_info=True)
                raise exc

        path_config = config_dict.get("paths", {})
        if not path_config:
            raise KeyError("Missing required 'paths' section in config.")

        # Path Settings (Using the same 'config_dict' everywhere)
        paths = cls.initialize_path_settings(project_root, path_config)

        sql = cls.initialize_sql_config(config_dict)

        log_cfg = cls.initialize_logging_config(config_dict)

        runtime = cls.initialize_runtime_paths(project_root, config_path, sql)

        api_cfg = config_dict.get("api", {})
        api = APIConfig(templates=(project_root / api_cfg["templates"]).resolve())

        logger.info(f"Configuration loaded successfully from {config_path}")

        return cls(project_root=project_root, paths=paths, sql=sql, runtime=runtime, logging=log_cfg, api=api)

    @classmethod
    def initialize_path_settings(cls, project_root, path_config):
        paths = PathSettings(
            raw_file=(project_root / path_config["raw_data"]).resolve(),
            processed_file=(project_root / path_config["processed_data"]).resolve(),
            database=(project_root / path_config["database"]).resolve(),
        )

        return paths

    @classmethod
    def initialize_runtime_paths(cls, project_root, config_path, sql):
        runtime = RuntimePaths(
            project_root=project_root,
            config_file=config_path.resolve(),
            logs_dir=(project_root / "logs").resolve(),
            sql_dir=(project_root / sql.root).resolve(),
        )

        return runtime

    @classmethod
    def initialize_logging_config(cls, config_dict):
        logging_config = config_dict.get("logging", {})
        log_cfg = LoggingConfig(
            level=cls._parse_log_level(logging_config.get("level", logging.INFO)),
            to_console=bool(logging_config.get("to_console", True)),
            ingestion_log=str(logging_config.get("ingestion_log", "ingest.log")),
            preprocessing_log=str(logging_config.get("preprocessing_log", "preprocess.log")),
        )

        return log_cfg

    @classmethod
    def initialize_sql_config(cls, config_dict):
        sql_config = config_dict.get("sql", {})
        try:
            tables_cfg = sql_config.get("tables", {})
            ep_cfg = sql_config.get("entrypoints", {})
            ep_data_cfg = ep_cfg.get("data", {})
            ep_api_cfg = ep_cfg.get("api", {})

            sql = SQLConfig(
                root=str(sql_config.get("root", "sql")),
                chunk_size=int(sql_config.get("chunk_size", 5000)),
                tables=SQLTables(
                    target=str(tables_cfg.get("target", "german_load_clean")),
                ),
                entrypoints=SQLEntrypoints(
                    data=SQLDataEntrypoints(
                        ingestion=SQLIngestionEntrypoints(
                            transform=str(ep_data_cfg.get("ingestion", {}).get("transform", "00_transform.sql")),
                        ),
                        preprocessing=SQLPreprocessingEntrypoints(
                            quality_check=str(
                                ep_data_cfg.get("preprocessing", {}).get("quality_check", "quality_check.sql")
                            ),
                        ),
                    ),
                    api=SQLApiEntrypoints(
                        target_view=str(ep_api_cfg.get("target_view", "target_view.sql")),
                    ),
                ),
            )
        except KeyError, ValueError, TypeError:
            logger.warning("Problems in reading SQL parameters, rolls back to the default values")
            sql = SQLConfig()
        return sql

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

    def sql_script_path(self, script_name: str) -> Path:
        """Resolve SQL script path under SQL root with recursive fallback lookup."""
        requested_path = Path(script_name)
        direct_candidate = (self.runtime.sql_dir / requested_path).resolve()

        if direct_candidate.exists():
            return direct_candidate

        exact_name_matches = sorted(self.runtime.sql_dir.rglob(requested_path.name))
        if len(exact_name_matches) == 1:
            return exact_name_matches[0].resolve()
        if len(exact_name_matches) > 1:
            candidates = ", ".join(str(path.relative_to(self.runtime.sql_dir)) for path in exact_name_matches)
            raise FileNotFoundError(f"Ambiguous SQL script '{script_name}'. Candidates under sql root: {candidates}")

        # Fallback for renamed/numbered SQL files, e.g. 00_transform.sql <-> transform.sql
        normalized_requested_name = re.sub(r"^\d+[_-]", "", requested_path.name)
        normalized_matches = sorted(
            path
            for path in self.runtime.sql_dir.rglob("*.sql")
            if re.sub(r"^\d+[_-]", "", path.name) == normalized_requested_name
        )

        if len(normalized_matches) == 1:
            return normalized_matches[0].resolve()
        if len(normalized_matches) > 1:
            candidates = ", ".join(str(path.relative_to(self.runtime.sql_dir)) for path in normalized_matches)
            raise FileNotFoundError(
                f"Ambiguous normalized SQL match for '{script_name}'. Candidates under sql root: {candidates}"
            )

        raise FileNotFoundError(
            f"SQL script '{script_name}' not found under {self.runtime.sql_dir}. "
            "Either create the file or point to an existing relative path in config.yml."
        )

    def transformation_sql_path(self) -> Path:
        return self.sql_script_path(self.sql.entrypoints.data.ingestion.transform)

    def quality_check_sql_path(self) -> Path:
        return self.sql_script_path(self.sql.entrypoints.data.preprocessing.quality_check)

    def api_target_view_sql_path(self) -> Path:
        return self.sql_script_path(self.sql.entrypoints.api.target_view)
