# configs/config_sql.py
"""
Setting up configuration for SQL
It will be handled by configs/main.py
"""

import logging
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class SQLTables(BaseModel):
    """Maps to sql.tables in config.yml."""

    model_config = ConfigDict(frozen=True)

    target: str = "german_load_clean"


class SQLIngestionEntrypoints(BaseModel):
    """Maps to sql.entrypoints.data.ingestion."""

    model_config = ConfigDict(frozen=True)

    transform: str = "00_transform.sql"


class SQLPreprocessingEntrypoints(BaseModel):
    """Maps to sql.entrypoints.data.preprocessing."""

    model_config = ConfigDict(frozen=True)

    quality_check: str = "quality_check.sql"


class SQLDataEntrypoints(BaseModel):
    """Maps to sql.entrypoints.data."""

    model_config = ConfigDict(frozen=True)

    ingestion: SQLIngestionEntrypoints = Field(default_factory=SQLIngestionEntrypoints)
    preprocessing: SQLPreprocessingEntrypoints = Field(default_factory=SQLPreprocessingEntrypoints)


class SQLApiEntrypoints(BaseModel):
    """Maps to sql.entrypoints.api."""

    model_config = ConfigDict(frozen=True)

    target_view: str = "target_view.sql"


class SQLEntrypoints(BaseModel):
    """Maps to sql.entrypoints."""

    model_config = ConfigDict(frozen=True)

    data: SQLDataEntrypoints = Field(default_factory=SQLDataEntrypoints)
    api: SQLApiEntrypoints = Field(default_factory=SQLApiEntrypoints)


class SQLConfig(BaseModel):
    """Maps to the sql section of config.yml exactly."""

    model_config = ConfigDict(frozen=True)

    root: str = "sql"
    chunk_size: int = 5000
    tables: SQLTables = Field(default_factory=SQLTables)
    entrypoints: SQLEntrypoints = Field(default_factory=SQLEntrypoints)


def initialize_sql_config(config_dict, logger: logging.Logger) -> SQLConfig:
    sql_config = config_dict.get("sql", {}) or {}
    try:
        sql = SQLConfig.model_validate(sql_config)
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("Problems in reading SQL parameters, rolls back to the default values")
        logger.debug("SQL config validation issue: %s", exc)
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
