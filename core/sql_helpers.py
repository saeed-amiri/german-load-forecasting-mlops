# core/sql_helpers.py
"""
Low-level helpers for handling DuckDB connections and Parquet export.
"""

import logging
import re
import warnings
from pathlib import Path
from typing import Mapping

import duckdb
import pandas as pd
from jinja2 import Template

logger = logging.getLogger(__name__)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str) -> str:
    """Validate SQL identifiers used for table aliases and names."""
    if not _IDENTIFIER_RE.fullmatch(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def _escape_sql_string(value: str) -> str:
    """Escape single quotes for SQL string literals."""
    return value.replace("'", "''")


def render_sql_template(sql_path: Path, context: Mapping[str, object]) -> str:
    """
    Load a SQL file and render it with Jinja2 context.
    """
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found at: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(**context)


def execute_and_export(conn: duckdb.DuckDBPyConnection, sql_query: str, output_path: Path) -> int:
    """
    Executes a SQL SELECT query and exports the result to a Parquet file.
    Returns the number of rows written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clean_sql = sql_query.strip().rstrip(";")
    escaped_output_path = _escape_sql_string(str(output_path))
    copy_sql = f"COPY ({clean_sql}) TO '{escaped_output_path}' (FORMAT PARQUET, COMPRESSION ZSTD);"
    conn.execute(copy_sql)

    count_df = conn.execute(f"SELECT COUNT(*) FROM '{escaped_output_path}'").fetchone()
    return count_df[0] if count_df else 0


def fetch_dataframe(conn: duckdb.DuckDBPyConnection, sql_query: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    """
    return conn.execute(sql_query).fetchdf()


def execute_sql(conn: duckdb.DuckDBPyConnection, query: str) -> None:
    """Execute a raw SQL query."""
    conn.execute(query)


def create_table_from_csv(conn: duckdb.DuckDBPyConnection, table_name: str, csv_path: Path) -> None:
    """Create or replace a table from a CSV file using DuckDB auto-detection."""
    safe_table_name = _validate_identifier(table_name)
    escaped_csv_path = _escape_sql_string(str(csv_path))
    conn.execute(f"CREATE OR REPLACE TABLE {safe_table_name} AS SELECT * FROM read_csv_auto('{escaped_csv_path}')")


def drop_table_if_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> None:
    """Drop a table if it exists."""
    safe_table_name = _validate_identifier(table_name)
    conn.execute(f"DROP TABLE IF EXISTS {safe_table_name}")


def get_table_stats(conn: duckdb.DuckDBPyConnection, table_name: str) -> dict[str, int]:
    """Return row and column counts for an existing table."""
    safe_table_name = _validate_identifier(table_name)
    rows_result = conn.execute(f"SELECT COUNT(*) FROM {safe_table_name}").fetchone()
    rows = int(rows_result[0]) if rows_result else 0

    cols_result = conn.execute(f"PRAGMA table_info('{safe_table_name}')").fetchall()
    return {"rows": rows, "columns": len(cols_result)}


def attach_legacy_sqlite(conn: duckdb.DuckDBPyConnection, sqlite_path: Path, alias: str = "legacy_db") -> None:
    """
    Attach a legacy SQLite database into a DuckDB session.
    """
    safe_alias = _validate_identifier(alias)
    escaped_sqlite_path = _escape_sql_string(str(sqlite_path))

    logger.info(f"Attaching SQLite database: {sqlite_path}")
    conn.execute("INSTALL sqlite;")
    conn.execute("LOAD sqlite;")
    conn.execute(f"CALL sqlite_attach('{escaped_sqlite_path}', attach_name='{safe_alias}', read_only=true);")


def attach_sqlite(conn: duckdb.DuckDBPyConnection, sqlite_path: Path, alias: str = "legacy_db") -> None:
    """Backward-compatible alias for attaching a legacy SQLite database."""
    warnings.warn(
        "attach_sqlite is deprecated; use attach_legacy_sqlite instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    attach_legacy_sqlite(conn=conn, sqlite_path=sqlite_path, alias=alias)
