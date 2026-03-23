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


def create_table_from_csv(conn: duckdb.DuckDBPyConnection, table_name: str, csv_path: Path) -> None:
    """
    Ingests a CSV into a table using DuckDB's specific auto-loader.
    """
    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
