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

from .sql_helpers import sql_executer, sql_validator

logger = logging.getLogger(__name__)


def run_model(config: PipelineConfig, script_name: str, target_table: str, layer_name: str) -> None:
    """Execute one SQL model and log the resulting row count."""
    sql_file_path = sql_script_path(script_name, config.runtime.sql_dir)
    logger.info(f"Executing {layer_name} model from {sql_file_path}...")
    count = sql_executer(config, sql_file_path, target_table, logger)
    logger.info(f"SUCCESS: Created '{target_table}' with {count} rows.")


def run_validation(config: PipelineConfig, logger: logging.Logger) -> None:
    """
    Runs quality checks against the database and logs a summary report.
    """

    sql_file_path = sql_script_path(config.sql.entrypoints.quality.data_quality_checks, config.runtime.sql_dir)

    try:
        stats_df: pd.DataFrame = sql_validator(config, sql_file_path, logger)

        if not stats_df.empty:
            report = stats_df.iloc[0].to_markdown()
            logger.info(f"\n--- Data Quality Report ---\n{report}")
        else:
            logger.warning("Quality check returned no data.")

    except Exception as err:
        logger.error(f"Validation failed: {err}")
        raise


def run_transformation(config: PipelineConfig) -> None:
    """
    fetch sql script and transform data from csv to a sql database
    """

    try:
        logger.info(f"Connecting to database at {config.paths.database}")
        run_model(
            config,
            config.sql.entrypoints.staging.stg_german_load,
            config.sql.tables.staging,
            "staging",
        )
        run_model(
            config,
            config.sql.entrypoints.features.fct_german_load,
            config.sql.tables.features,
            "features",
        )
        run_model(
            config,
            config.sql.entrypoints.marts.german_load_api,
            config.sql.tables.marts,
            "marts",
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

    run_validation(config, logger)


if __name__ == "__main__":
    run_preprocessing()
