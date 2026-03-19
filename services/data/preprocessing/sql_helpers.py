# services/data/preprocessing/sql_helpers.py
"""
Low-level helpers for handling SQL database connections and execution.
"""

import sqlite3
from pathlib import Path

import pandas as pd
from jinja2 import Template


def render_sql_template(sql_path: Path, context: dict) -> str:
    """
    Load a SQL file and render it with Jinja2 context.

    Args:
        sql_path: Path to the .sql file.
        context: Dictionary of variables to inject into the template.

    Returns:
        The rendered SQL string.
    """
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found at: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(**context)


def execute_script(database: Path, sql_query: str, target_table: str) -> int:
    """
    Executes a multi-statement SQL script (CREATE, INSERT, etc.)
    and returns the row count of the target table.

    Args:
        database: Path to the SQLite database file.
        sql_query: The SQL script to execute.
        target_table: The table name to count rows for after execution.

    Returns:
        The number of rows in the target table.
    """
    db_path = str(database)

    with sqlite3.connect(db_path) as conn:
        # Execute the main transformation script
        conn.executescript(sql_query)

        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{target_table}"')
        count = cursor.fetchone()[0]

    return count


def fetch_dataframe(database: Path, sql_query: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    Useful for validation and statistics gathering.
    """
    db_path = str(database)
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(sql_query, conn)

    return df
