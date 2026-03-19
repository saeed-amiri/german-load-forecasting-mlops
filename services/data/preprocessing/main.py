# services/data/preprocessing/main.py
"""
Main orchestrator for the data preprocessing pipeline.
"""

import logging
from pathlib import Path

from configs.config_logs import resolve_service_log_path
from configs.config_sql import sql_script_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from .sql_helpers import execute_script, fetch_dataframe, render_sql_template

logger = logging.getLogger(__name__)


def _get_sql_context(config: PipelineConfig) -> dict:
    """
    Constructs the Jinja context dictionary from the pipeline configuration.
    """
    return {
        "staging_table": config.sql.tables.staging,
        "features_table": config.sql.tables.features,
    }


def run_model(config: PipelineConfig, script_name: str, target_table: str, layer_name: str) -> None:
    """
    Execute a SQL model, log the result, and handle errors.
    """
    sql_file_path = sql_script_path(script_name, config.runtime.sql_dir)
    context = _get_sql_context(config)

    logger.info(f"Executing {layer_name} model from {sql_file_path}...")

    # Render and Execute
    sql_query = render_sql_template(sql_file_path, context)
    row_count = execute_script(config.paths.database, sql_query, target_table)

    logger.info(f"SUCCESS: Created '{target_table}' with {row_count} rows.")


def log_table_overview(config: PipelineConfig) -> None:
    """
    Runs quality checks against the database and logs a summary report.
    """
    database: Path = config.paths.database
    context = _get_sql_context(config)

    sql_file_path = sql_script_path(config.sql.entrypoints.quality.target_overview, config.runtime.sql_dir)

    try:
        sql_query = render_sql_template(sql_file_path, context)
        stats_df = fetch_dataframe(database, sql_query)

        if not stats_df.empty:
            report = stats_df.iloc[0].to_markdown()
            logger.info(f"\n--- Target Overview ---\n{report}")
        else:
            logger.warning("Target Overview query returned no data.")

    except Exception as err:
        logger.error(f"Validation failed: {err}")
        raise RuntimeError("Loading and loging from SQL scripts failed!") from err


def run_transformation(config: PipelineConfig) -> None:
    """
    Orchestrates the transformation steps.
    """
    logger.info(f"Connecting to database at {config.paths.database}")

    # Run the features model
    run_model(
        config,
        config.sql.entrypoints.features.fct_german_load,
        config.sql.tables.features,
        "features",
    )


def run_preprocessing() -> None:
    """
    Entry point for the preprocessing service.
    """
    # Setup Config
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))

    # Setup Logging
    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "preprocessing")
    setup_logging(
        log_file=log_path,
        level=config.logging.level,
        # Note: Keeping the user's argument name 'to_consle' assuming it exists in their library
        to_consle=config.logging.to_console,
    )

    logger.info("Starting preprocessing-pipeline execution...")

    try:
        run_transformation(config)
        log_table_overview(config)
        logger.info("Pipeline finished successfully.")

    except Exception as err:
        logger.critical("Pipeline execution failed!", exc_info=True)
        # Re-raise to ensure the process exits with a non-zero code if needed
        raise RuntimeError(f"Preprocessing Service Failure: {err}") from err


if __name__ == "__main__":
    run_preprocessing()
