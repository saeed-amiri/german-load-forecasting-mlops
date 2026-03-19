# services/data/ingestion/main.py
"""
Ingestion Service.

Loads raw CSV, persists it to a temporary SQL table,
and executes the transformation script to create the clean staging table.
"""

import logging
from pathlib import Path

import pandas as pd
from jinja2 import Template

from configs.config_logs import resolve_service_log_path
from configs.config_sql import sql_script_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from .io_helpers import drop_table, execute_sql_script, load_csv_data, write_df_to_table

logger = logging.getLogger(__name__)


def run_ingestion() -> None:
    """
    Main entry point.
    """
    # 1. Setup
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "ingestion")
    setup_logging(log_file=log_path, level=config.logging.level, to_consle=config.logging.to_console)

    logger.info("Starting ingestion-pipeline execution...")

    try:
        # Define table names from config
        raw_table = config.sql.tables.raw_source_table
        staging_table = config.sql.tables.staging

        # 2. Load Raw CSV
        logger.info(f"Reading CSV from {config.paths.raw_file}...")
        df = load_csv_data(config.paths.raw_file)

        # Add metadata
        df["ingested_at"] = pd.Timestamp.now()

        # 3. Write to Temporary "Raw" Table
        logger.info(f"Writing raw data to temporary table '{raw_table}'...")
        write_df_to_table(
            df=df, database_path=config.paths.database, table_name=raw_table, chunk_size=config.sql.chunk_size
        )

        # 4. Prepare and Execute SQL Transformation
        sql_file_path = sql_script_path(config.sql.entrypoints.staging.stg_german_load, config.runtime.sql_dir)

        with open(sql_file_path, "r") as f:
            template = Template(f.read())

        context = {"raw_source_table": raw_table, "staging_table": staging_table}
        sql_query = template.render(**context)

        logger.info("Executing staging transformation...")
        execute_sql_script(config.paths.database, sql_query)

        # 5. Cleanup
        logger.info(f"Dropping temporary table '{raw_table}'...")
        drop_table(config.paths.database, raw_table)

        logger.info(f"SUCCESS: Staging table '{staging_table}' created and populated.")

    except Exception as err:
        logger.critical("Ingestion pipeline failed!", exc_info=True)
        raise RuntimeError(f"Ingestion Service Failure: {err}") from err


if __name__ == "__main__":
    run_ingestion()
