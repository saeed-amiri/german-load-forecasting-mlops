# services/data/preprocessing/main.py
"""
Main orchestrator for the data preprocessing pipeline.
Responsible for transforming data from Staging -> Features.
"""

import logging
from pathlib import Path

from configs.config_logs import resolve_service_log_path
from configs.config_sql import sql_script_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from core.sql_helpers import execute_script, fetch_dataframe, render_sql_template

logger = logging.getLogger(__name__)


def run_model(config: PipelineConfig, script_name: str, target_table: str, layer_name: str) -> None:
    """Execute one SQL model and log the resulting row count."""
    sql_file_path = sql_script_path(script_name, config.runtime.sql_dir)

    # Context for Preprocessing: Source is Staging, Target is Features
    context = {
        "staging_table": config.sql.tables.staging.load,
        "features_table": config.sql.tables.features.load,
    }

    logger.info(f"Executing {layer_name} model from {sql_file_path}...")

    sql_query = render_sql_template(sql_file_path, context)
    count = execute_script(config.paths.database, sql_query, target_table)

    logger.info(f"SUCCESS: Created '{target_table}' with {count} rows.")


def log_table_overview(config: PipelineConfig) -> None:
    """Runs quality checks against the Features table."""
    database: Path = config.paths.database
    context = {"features_table": config.sql.tables.features.load}

    target_overview = sql_script_path(config.sql.entrypoints.features.load_log, config.runtime.sql_dir)

    try:
        sql_query = render_sql_template(target_overview, context)
        stats_df = fetch_dataframe(database, sql_query)

        if not stats_df.empty:
            report = stats_df.iloc[0].to_markdown()
            logger.info(f"\n--- Features Overview ---\n{report}")
        else:
            logger.warning("Features Overview returned no data.")

    except Exception as err:
        logger.error(f"Validation failed: {err}")
        raise


def run_transformation(config: PipelineConfig) -> None:
    """Fetch SQL script and transform data from Staging to Features."""
    logger.info(f"Connecting to database at {config.paths.database}")

    # Only run the Features model
    run_model(
        config,
        config.sql.entrypoints.features.load,
        config.sql.tables.features.load,
        "features",
    )


def run_preprocessing() -> None:
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "preprocessing")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting preprocessing-pipeline execution...")

    try:
        run_transformation(config)
        log_table_overview(config)
    except Exception as err:
        logger.critical("Pipeline execution failed!", exc_info=True)
        raise RuntimeError(f"Preprocessing Service Failure: {err}") from err


if __name__ == "__main__":
    run_preprocessing()
