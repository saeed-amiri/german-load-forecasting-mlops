# services/datapreprocessing/sql_helpers.py
"""
Helpers for handling the sql related job for preprocessing
"""
import logging
from pathlib import Path

import sqlite3

from core.config import PipelineConfig


def fetch_sql_script_path(config: PipelineConfig, project_root: Path) -> Path:
    """
    Resolves and validates the absolute path to the SQL transformation script.

    Raises:
        FileNotFoundError: If the SQL file defined in config does not exist.
    """
    sql_file_path: Path = project_root / "services/data/sql" / config.sql.transform

    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL transformation script missing at {sql_file_path}")

    return sql_file_path


def execute_sql_transformation(config: PipelineConfig, sql_file_path: Path, logger: logging.Logger) -> int:
    """
    Executes a multi-statement SQL script and returns the resulting row count.

    Transactions are handled automatically by the connection context manager.
    """
    with sqlite3.connect(config.paths.database) as conn:
        logger.info(f"Reading SQL script from {sql_file_path}")

        with open(sql_file_path, 'r', encoding="utf8") as sql:
            sql_query = sql.read()

        conn.executescript(sql_query)

        # Verify
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {config.sql.table_name}")
        count = cursor.fetchone()[0]
    return count
