# configs/config_sql.py
"""
Setting up configuration for SQL.
It will be handled by configs/main.py.
"""

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class SQLTables(BaseModel):
    """Maps to sql.tables in config.yml."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    raw_source_table: str = "raw_source_data"
    staging: str = "stg_german_load"
    features: str = "fct_german_load"
    marts: str = "german_load_api"


class SQLStagingEntrypoints(BaseModel):
    """Maps to sql.entrypoints.staging."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stg_german_load: str = "staging/stg_german_load.sql"


class SQLFeaturesEntrypoints(BaseModel):
    """Maps to sql.entrypoints.features."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fct_german_load: str = "features/fct_german_load.sql"


class SQLMartsEntrypoints(BaseModel):
    """Maps to sql.entrypoints.marts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    german_load_api: str = "marts/german_load_api.sql"


class SQLQualityEntrypoints(BaseModel):
    """Maps to sql.entrypoints.quality."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_overview: str = "quality/target_overview.sql"


class SQLEntrypoints(BaseModel):
    """Maps to sql.entrypoints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    staging: SQLStagingEntrypoints = Field(default_factory=SQLStagingEntrypoints)
    features: SQLFeaturesEntrypoints = Field(default_factory=SQLFeaturesEntrypoints)
    marts: SQLMartsEntrypoints = Field(default_factory=SQLMartsEntrypoints)
    quality: SQLQualityEntrypoints = Field(default_factory=SQLQualityEntrypoints)


class SQLConfig(BaseModel):
    """Maps to the sql section of config.yml exactly."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: str = "sql"
    chunk_size: int = 50000
    tables: SQLTables = Field(default_factory=SQLTables)
    entrypoints: SQLEntrypoints = Field(default_factory=SQLEntrypoints)


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
