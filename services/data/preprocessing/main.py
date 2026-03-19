# services/data/preprocessing/main.py
"""
Loading sql script for transfering data into a table
"""

import logging
from pathlib import Path

import pandas as pd

from configs.config_logs import resolve_service_log_path
from configs.config_sql import sql_script_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from .sql_helpers import sql_executer, overview_tables

logger = logging.getLogger(__name__)


def run_model(config: PipelineConfig, script_name: str, target_table: str, layer_name: str) -> None:
    """Execute one SQL model and log the resulting row count."""
    sql_file_path = sql_script_path(script_name, config.runtime.sql_dir)
    logger.info(f"Executing {layer_name} model from {sql_file_path}...")

    count = sql_executer(config.paths.database, sql_file_path, target_table, logger)
    logger.info(f"SUCCESS: Created '{target_table}' with {count} rows.")


def log_table_overview(config: PipelineConfig, logger: logging.Logger) -> None:
    """
    Runs quality checks against the database and logs a summary report.
    """
    database: Path = config.paths.database

    target_overview = sql_script_path(config.sql.entrypoints.quality.target_overview, config.runtime.sql_dir)
    overview_tables(database=database, sql_file_path=target_overview, msg='Target', logger=logger)


def run_transformation(config: PipelineConfig) -> None:
    """
    fetch sql script and transform data from csv to a sql database
    """

    try:
        logger.info(f"Connecting to database at {config.paths.database}")
        run_model(
            config,
            config.sql.entrypoints.features.fct_german_load,
            config.sql.tables.features,
            "features",
        )

    except Exception as err:
        logger.critical("Transformation failed!", exc_info=True)
        raise RuntimeError(f"Transformation Service Failure: {err}") from err


def run_preprocessing() -> None:
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "preprocessing")
    setup_logging(log_file=log_path, level=config.logging.level, to_consle=config.logging.to_console)

    logger.info("Starting preprocessing-pipeline execution...")

    run_transformation(config)

    log_table_overview(config, logger)


if __name__ == "__main__":
    run_preprocessing()
