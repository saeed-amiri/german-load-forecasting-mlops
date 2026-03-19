"""
IO helper functions for ingestion of raw data
"""

import logging
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from configs.main import PipelineConfig


def load_raw_data(config: PipelineConfig, logger: logging.Logger) -> pd.DataFrame:
    """
    Loads raw data from a CSV file defined in the configuration.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file is empty or corrupted.
        RuntimeError: For unexpected OS-level IO issues.
    """
    file_path = Path(config.paths.raw_file)

    if not file_path.exists():
        logger.error(f"Data source missing: {file_path.absolute()}")
        raise FileNotFoundError(f"No file found at {file_path}")

    try:
        df = pd.read_csv(file_path, low_memory=False)

        if df.empty:
            logger.warning(f"File at {file_path} is empty.")

        return df

    except pd.errors.EmptyDataError as err:
        logger.error(f"File is empty: {file_path}")
        raise ValueError("Target CSV contains no data.") from err

    except Exception as err:
        logger.exception(f"Unexpected error loading {file_path}")
        raise RuntimeError("Failed to load pipeline data.") from err


def save_to_sqlite(df: pd.DataFrame, config: PipelineConfig, logger: logging.Logger) -> None:
    """
    Persists DataFrame to a SQLite database with transactional integrity.

    Args:
        df: The source DataFrame.
        target_table: Target table in SQLite.
        db_path: Path to the .db or .sqlite file.
    """
    stg_table: str = config.sql.entrypoints.staging.stg_german_load
    if df.empty:
        logger.warning(f"No data to save for table '{stg_table}'. Skipping.")
        return

    try:
        with closing(sqlite3.connect(config.paths.database)) as conn:
            with conn:
                df.to_sql(name=stg_table, con=conn, if_exists="replace", index=False, chunksize=config.sql.chunk_size)

        logger.info(f"Successfully updated '{stg_table}' with {len(df)} rows.")

    except sqlite3.Error as err:
        logger.error(f"SQLite Database error for '{stg_table}': {err}")
        raise RuntimeError(f"Failed to write to SQLite at {config.paths.database}") from err
