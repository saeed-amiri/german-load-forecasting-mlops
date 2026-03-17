# services/data/preprocessing/main.py
"""
Loading sql script for transfering data into a table
"""

import logging
from pathlib import Path

import pandas as pd

from core.config import PipelineConfig

from .sql_helpers import sql_executer, sql_validator

logger = logging.getLogger(__name__)

def run_validation(config: PipelineConfig, logger: logging.Logger) -> None:
    """
    Runs quality checks against the database and logs a summary report.
    """

    sql_file_path = config.quality_check_sql_path()

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
        sql_file_path = config.transformation_sql_path()

        logger.info(f"Executing transformation on {config.paths.database}...")
        count = sql_executer(config, sql_file_path, logger)

        logger.info(f"SUCCESS: Created '{config.sql.tables.target}' with {count} rows.")

    except Exception as err:
        logger.critical("Transformation failed!", exc_info=True)
        raise RuntimeError(f"Transformation Service Failure: {err}") from err


def run_preprocessing() -> None:
    config = PipelineConfig.load(config_name="config", start_file=Path(__file__))
    config.setup_service_logging("preprocessing")

    logger.info("Starting preprocessing-pipeline execution...")

    run_transformation(config)

    run_validation(config, logger)


if __name__ == "__main__":
    run_preprocessing()
