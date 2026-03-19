# services/data/marts/main.py
"""
Marts Service.
Responsible for creating aggregated tables (Data Marts) for consumption by the API.
Dependencies: Preprocessing Service (must run first).
"""

import logging
from pathlib import Path

from configs.config_logs import resolve_service_log_path
from configs.config_sql import sql_script_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

# We reuse the sql_helpers from preprocessing as they are generic utilities
from core.sql_helpers import execute_script, render_sql_template

logger = logging.getLogger(__name__)


def run_marts_pipeline() -> None:
    """
    Entry point for the marts pipeline.
    """
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "marts")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting Marts pipeline execution...")

    try:
        sql_file_path = sql_script_path(config.sql.entrypoints.marts.german_load_api, config.runtime.sql_dir)

        # Context only needs the source (features) and target (marts)
        context = {"features_table": config.sql.tables.features, "marts_table": config.sql.tables.marts}

        logger.info(f"Building mart table '{config.sql.tables.marts}'...")

        sql_query = render_sql_template(sql_file_path, context)
        count = execute_script(config.paths.database, sql_query, config.sql.tables.marts)

        logger.info(f"SUCCESS: Mart table created with {count} rows.")

    except Exception as err:
        logger.critical("Marts pipeline failed!", exc_info=True)
        raise RuntimeError(f"Marts Service Failure: {err}") from err


if __name__ == "__main__":
    run_marts_pipeline()
