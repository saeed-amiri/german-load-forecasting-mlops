# configs/config_sql.py
"""
Setting up configuration for SQL
It will be handle by configs/main.py
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path


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


def initialize_sql_config(config_dict, logger: logging.Logger) -> SQLConfig:
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


def sql_script_path(script_name: str, sql_dir: Path) -> Path:
    """Resolve SQL script path under SQL root with recursive fallback lookup."""
    requested_path = Path(script_name)
    direct_candidate = (sql_dir / requested_path).resolve()

    if direct_candidate.exists():
        return direct_candidate

    exact_name_matches = sorted(sql_dir.rglob(requested_path.name))
    if len(exact_name_matches) == 1:
        return exact_name_matches[0].resolve()
    if len(exact_name_matches) > 1:
        candidates = ", ".join(str(path.relative_to(sql_dir)) for path in exact_name_matches)
        raise FileNotFoundError(f"Ambiguous SQL script '{script_name}'. Candidates under sql root: {candidates}")

    # Fallback for renamed/numbered SQL files, e.g. 00_transform.sql <-> transform.sql
    normalized_requested_name = re.sub(r"^\d+[_-]", "", requested_path.name)
    normalized_matches = sorted(
        path for path in sql_dir.rglob("*.sql") if re.sub(r"^\d+[_-]", "", path.name) == normalized_requested_name
    )

    if len(normalized_matches) == 1:
        return normalized_matches[0].resolve()
    if len(normalized_matches) > 1:
        candidates = ", ".join(str(path.relative_to(sql_dir)) for path in normalized_matches)
        raise FileNotFoundError(
            f"Ambiguous normalized SQL match for '{script_name}'. Candidates under sql root: {candidates}"
        )

    raise FileNotFoundError(
        f"SQL script '{script_name}' not found under {sql_dir}. "
        "Either create the file or point to an existing relative path in config.yml."
    )
