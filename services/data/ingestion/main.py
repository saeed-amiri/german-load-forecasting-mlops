# services/data/ingestion/main.py

import logging
import time
from pathlib import Path

import duckdb
from jinja2 import Template

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from .context import SourceContext
from .database import create_table_from_csv, execute_sql, get_table_stats

logger = logging.getLogger(__name__)


def process_source(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> None:
    """
    Loads full CSV into permanent Raw table, then transforms to Staging.
    Logs detailed stats for audit.
    """
    try:
        logger.info(f"Processing source: {ctx.source_name}")

        raw_table = ctx.raw_table
        staging_table = ctx.staging_table

        logger.info(f"Loading full CSV into permanent raw table '{raw_table}'...")
        create_table_from_csv(conn, raw_table, csv_path=ctx.raw_file)

        raw_stats = get_table_stats(conn, raw_table)
        logger.info(
            f"RAW TABLE CREATED | Name: '{raw_table}' | Rows: {raw_stats['rows']:,} | Columns: {raw_stats['columns']}"
        )

        with open(ctx.sql_template_path, "r", encoding="utf8") as f:
            template = Template(f.read())

        sql_query = template.render(
            raw_source_table=raw_table,
            staging_table=staging_table,
            columns=ctx.columns,
            timestamp_raw=ctx.timestamp_column,
        )

        logger.info("Executing staging transformation...")
        execute_sql(conn, sql_query)

        staging_stats = get_table_stats(conn, staging_table)
        logger.info(
            f"STAGING TABLE CREATED | Name: '{staging_table}' | "
            f"Rows: {staging_stats['rows']:,} | Columns: {staging_stats['columns']}"
        )

        logger.info(f"DATABASE FILE: {ctx.database}")

        logger.info(f"SCHEMA MAPPING for '{staging_table}':")
        for col in ctx.columns:
            logger.info(f"  -> {col.raw:<40} | {col.clean}")

        logger.info(f"SUCCESS: Source '{ctx.source_name}' processed.")

    except Exception as err:
        logger.error(f"Failed to process source '{ctx.source_name}'", exc_info=True)
        raise RuntimeError(f"Processing {ctx.raw_file} Failed!") from err


def run_ingestion() -> None:
    """
    Main entry point for ingestion.
    """
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "ingestion")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting ingestion-pipeline execution...")
    source_names = list(config.sql.sources.keys())
    errors = []

    with duckdb.connect(str(config.paths.database)) as conn:
        for name in source_names:
            start_time = time.perf_counter()

            try:
                ctx = SourceContext.from_config(name, config)
                process_source(conn, ctx)

            except Exception:
                logger.error(f"Failed to process source '{name}'", exc_info=True)
                errors.append(name)

            duration = time.perf_counter() - start_time
            logger.info(f"Finished '{name}' in {duration:.2f} seconds")

    if errors:
        raise RuntimeError(f"Ingestion failed for sources: {errors}")


if __name__ == "__main__":
    run_ingestion()
