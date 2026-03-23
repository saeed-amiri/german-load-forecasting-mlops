# services/data/ingestion/io_helpers.py
"""
IO helper functions for ingestion.
DuckDB-native ingestion: no pandas, no chunking, no memory blowups.
"""

from pathlib import Path

import duckdb


def write_csv_to_table(csv_path: Path, database_path: Path, table_name: str) -> None:
    """
    DuckDB-native CSV ingestion.
    Reads CSV directly using DuckDB's vectorized engine.
    Zero memory overhead, extremely fast.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Data source missing: {csv_path}")

    with duckdb.connect(str(database_path)) as conn:
        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT *, now() AS ingested_at
            FROM read_csv_auto('{csv_path}', header=True);
        """)


def execute_sql_script(database_path: Path, sql_query: str) -> None:
    """Executes SQL in DuckDB."""
    with duckdb.connect(str(database_path)) as conn:
        conn.execute(sql_query)


def drop_table(database_path: Path, table_name: str) -> None:
    """Drops a table if it exists."""
    with duckdb.connect(str(database_path)) as conn:
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
