# core/sql_helpers.py
"""
Low-level helpers for handling DuckDB connections and Parquet export.
"""

import logging
from pathlib import Path

import duckdb
import pandas as pd
from jinja2 import Template

logger = logging.getLogger(__name__)


def render_sql_template(sql_path: Path, context: dict) -> str:
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
    copy_sql = f"COPY ({clean_sql}) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD);"
    conn.execute(copy_sql)

    count_df = conn.execute(f"SELECT COUNT(*) FROM '{output_path}'").fetchone()
    return count_df[0] if count_df else 0


def fetch_dataframe(conn: duckdb.DuckDBPyConnection, sql_query: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    """
    return conn.execute(sql_query).fetchdf()


def attach_sqlite(conn: duckdb.DuckDBPyConnection, sqlite_path: Path, alias: str = "legacy_db") -> None:
    """
    Optional: Helper to attach an old SQLite database if you need to migrate data.
    """
    logger.info(f"Attaching SQLite database: {sqlite_path}")
    conn.execute("INSTALL sqlite;")
    conn.execute("LOAD sqlite;")
    conn.execute(f"CALL sqlite_attach('{sqlite_path}', attach_name='{alias}', read_only=true);")
