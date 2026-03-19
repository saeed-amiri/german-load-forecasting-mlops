# services/datapreprocessing/sql_helpers.py
"""
Helpers for handling the sql related job for preprocessing
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from configs.main import PipelineConfig
from configs.config_sql import sql_script_path


def sql_executer(config: PipelineConfig, sql_file_path: Path, target_table: str, logger: logging.Logger) -> int:
    """
    Executes a multi-statement SQL script and returns the resulting row count.

    Transactions are handled automatically by the connection context manager.
    """
    with sqlite3.connect(config.paths.database) as conn:
        logger.info(f"Reading SQL script from {sql_file_path}")

        with open(sql_file_path, "r", encoding="utf8") as sql:
            sql_query = sql.read()

        conn.executescript(sql_query)

        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
        count = cursor.fetchone()[0]
    return count


def sql_validator(config: PipelineConfig, sql_file_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """
    Executes a SQL script via pandas to validate the data
    """

    if not sql_file_path.exists():
        raise FileNotFoundError(f"Quality check script missing: {sql_file_path}")

    with open(sql_file_path, "r", encoding="utf8") as f:
        sql_query = f.read()

    with sqlite3.connect(config.paths.database) as conn:
        stats_df = pd.read_sql(sql_query, conn)

    return stats_df


def overview_target(config: PipelineConfig, logger: logging.Logger) -> None:
    """
    Log an overview of the target table
    """
    sql_file_path = sql_script_path(config.sql.entrypoints.quality.target_overview, config.runtime.sql_dir)

    try:
        stats_df: pd.DataFrame = sql_validator(config, sql_file_path, logger)

        if not stats_df.empty:
            report = stats_df.iloc[0].to_markdown()
            logger.info(f"\n--- Target Overivew ---\n{report}")
        else:
            logger.warning("Target Overivew returned no data.")

    except Exception as err:
        logger.error(f"Validation failed: {err}")
        raise