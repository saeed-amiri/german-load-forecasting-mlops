# services/data/ingestion/io_helpers.py
"""
IO helper functions for ingestion.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


def load_csv_data(file_path: Path) -> pd.DataFrame:
    """
    Loads raw data from a CSV file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data source missing: {file_path}")

    try:
        df = pd.read_csv(file_path, low_memory=False)
        if df.empty:
            raise ValueError(f"File at {file_path} is empty.")
        return df
    except Exception as err:
        raise RuntimeError(f"Failed to read CSV: {err}") from err


def write_df_to_table(df: pd.DataFrame, database_path: Path, table_name: str, chunk_size: int) -> None:
    """
    Writes a DataFrame to a specific table in the SQLite database.
    """
    with closing(sqlite3.connect(str(database_path))) as conn:
        with conn:
            df.to_sql(name=table_name, con=conn, if_exists="replace", index=False, chunksize=chunk_size)


def execute_sql_script(database_path: Path, sql_query: str) -> None:
    """
    Executes a raw SQL script (multiple statements) in the database.
    """
    with sqlite3.connect(str(database_path)) as conn:
        conn.executescript(sql_query)


def drop_table(database_path: Path, table_name: str) -> None:
    """
    Drops a table if it exists.
    """
    with sqlite3.connect(str(database_path)) as conn:
        cursor = conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        conn.commit()
