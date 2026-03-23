# configs/config_sql.py

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------
# 1. Generic building blocks
# ---------------------------------------------------------


class ColumnMapping(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    raw: str
    clean: str


class TableNames(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __getattr__(self, item):
        data = self.model_dump()
        try:
            return data[item]
        except KeyError:
            raise AttributeError(item)


class SQLNames(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __getattr__(self, item):
        data = self.model_dump()
        try:
            return data[item]
        except KeyError:
            raise AttributeError(item)


class StageConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tables: TableNames = Field(default_factory=TableNames)
    sql_files: SQLNames = Field(default_factory=SQLNames)


# ---------------------------------------------------------
# 2. Schema for ONE data source
# ---------------------------------------------------------


class DataSourceConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    frequency: str
    timestamp: str
    raw_path: str

    columns: list[ColumnMapping] = Field(default_factory=list)

    staging: StageConfig = Field(default_factory=StageConfig)
    features: StageConfig = Field(default_factory=StageConfig)
    marts: StageConfig = Field(default_factory=StageConfig)


# ---------------------------------------------------------
# 3. Wrapper for dot-notation access to sources
# ---------------------------------------------------------


class DataSources(BaseModel):
    """
    A wrapper around a dict[str, DataSourceConfig] that supports:
        - dot notation: sources.load
        - dict access: sources["load"]
    """

    model_config = ConfigDict(extra="forbid")

    data: dict[str, DataSourceConfig] = Field(default_factory=dict)

    def __getattr__(self, item):
        try:
            return self.data[item]
        except KeyError:
            raise AttributeError(item)

    def __getitem__(self, item):
        return self.data[item]

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()


# ---------------------------------------------------------
# 4. Top-level SQL config
# ---------------------------------------------------------


class SQLConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    root: str = "sql"
    chunk_size: int = 50000
    sources: DataSources


# ---------------------------------------------------------
# 5. SQL script resolver
# ---------------------------------------------------------


def sql_script_path(script_name: str, sql_dir: Path) -> Path:

    requested_path = Path(script_name)
    direct_candidate = (sql_dir / requested_path).resolve()

    if direct_candidate.exists():
        return direct_candidate

    exact_matches = sorted(sql_dir.rglob(requested_path.name))
    if len(exact_matches) == 1:
        return exact_matches[0].resolve()
    if len(exact_matches) > 1:
        candidates = ", ".join(str(p.relative_to(sql_dir)) for p in exact_matches)
        raise FileNotFoundError(f"Ambiguous SQL script '{script_name}'. Candidates: {candidates}")

    normalized = re.sub(r"^\d+[_-]", "", requested_path.name)
    normalized_matches = sorted(p for p in sql_dir.rglob("*.sql") if re.sub(r"^\d+[_-]", "", p.name) == normalized)

    if len(normalized_matches) == 1:
        return normalized_matches[0].resolve()
    if len(normalized_matches) > 1:
        candidates = ", ".join(str(p.relative_to(sql_dir)) for p in normalized_matches)
        raise FileNotFoundError(f"Ambiguous normalized SQL match for '{script_name}'. Candidates: {candidates}")

    raise FileNotFoundError(
        f"SQL script '{script_name}' not found under {sql_dir}. Either create the file or update config.yml."
    )
