"""
Run the ingestion pipeline from raw source files into staging tables.

The module coordinates source-by-source ingestion by building a context from
configuration, loading each raw file into DuckDB, applying the source-specific
staging SQL template, and emitting audit logs for row/column counts and schema
mapping.
"""

import logging
import time
from pathlib import Path

import duckdb

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging
from core.sql_helpers import create_table_from_csv, execute_sql, get_table_stats, render_sql_template

from .context import SourceContext

logger = logging.getLogger(__name__)


def process_source(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> None:
    """
    Process one configured source into raw and staging tables.

    Steps:
    1. Load the source CSV into the source raw table.
    2. Render and execute the staging SQL template for that source.
    3. Log table statistics and column mapping for auditability.

    Raises:
        RuntimeError: If any step fails for the current source.
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

        sql_query = render_sql_template(
            ctx.sql_template_path,
            context={
                "raw_source_table": raw_table,
                "staging_table": staging_table,
                "columns": ctx.columns,
                "timestamp_raw": ctx.timestamp_column,
            },
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
        raise RuntimeError(f"Processing source '{ctx.source_name}' failed for file: {ctx.raw_file}") from err


def run_ingestion() -> None:
    """
    Execute ingestion for all configured sources.

    The function initializes config and logging, opens one DuckDB connection,
    processes each source independently, and collects failures so one source
    error does not stop the remaining sources. If any source fails, it raises
    a summary RuntimeError at the end.
    """
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "ingestion")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting ingestion-pipeline execution...")
    source_names = list(config.sql.sources.keys())
    errors: list[str] = []

    with duckdb.connect(str(config.paths.database)) as conn:
        for name in source_names:
            start_time = time.perf_counter()

            try:
                ctx = SourceContext.from_config(name, config)
                process_source(conn, ctx)

            except Exception as err:
                logger.error("Failed to process source '%s': %s", name, err, exc_info=True)
                errors.append(name)

            duration = time.perf_counter() - start_time
            logger.info(f"Finished '{name}' in {duration:.2f} seconds")

    if errors:
        raise RuntimeError(f"Ingestion failed for sources: {errors}")


if __name__ == "__main__":
    run_ingestion()
