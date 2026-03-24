# services/data/ingestion/database.py
"""
IO helper functions for ingestion.
"""

from pathlib import Path

import duckdb


def execute_sql(conn: duckdb.DuckDBPyConnection, query: str) -> None:
    """Executes a raw SQL query."""
    conn.execute(query)


def drop_table(conn: duckdb.DuckDBPyConnection, table_name: str) -> None:
    """Drops a table if it exists."""
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")


def create_table_from_csv(conn: duckdb.DuckDBPyConnection, raw_table: str, csv_path: Path) -> None:
    """
    Ingests a CSV into a table using DuckDB's specific auto-loader.
    """
    conn.execute(f"CREATE OR REPLACE TABLE {raw_table} AS SELECT * FROM read_csv_auto('{csv_path}')")


def get_table_stats(conn: duckdb.DuckDBPyConnection, table_name: str) -> dict:
    """
    Returns row count and column count for a specific table.
    """
    try:
        rows = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]

        cols_result = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        cols = len(cols_result)

        return {"rows": rows, "columns": cols}

    except Exception:
        return {"rows": 0, "columns": 0}
