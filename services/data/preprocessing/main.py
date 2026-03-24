# services/data/preprocessing/main.py
"""
Main orchestrator for the data preprocessing pipeline.
Responsible for transforming data from Staging -> Parquet Features.
"""

import logging
import time
from pathlib import Path

import duckdb

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging
from core.sql_helpers import execute_and_export, render_sql_template

from .context import SourceContext

logger = logging.getLogger(__name__)


def log_parquet_overview(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> None:
    """Runs quality checks against the generated Parquet file using the SQL template."""

    context = {"target_table": f"'{ctx.output}'"}

    try:
        sql_query = render_sql_template(ctx.sql_path_log, context)
        clean_sql = sql_query.strip().rstrip(";")
        stats_df = conn.execute(clean_sql).fetchdf()

        if not stats_df.empty:
            report = stats_df.iloc[0].to_markdown()
            logger.info(f"\n--- Features Overview ({ctx.source_name}) ---\n{report}")
        else:
            logger.warning("Features Overview returned no data.")

    except Exception as err:
        logger.error(f"Validation failed: {err}")
        raise


def run_transformation(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> int:
    """Executes SQL and exports to Parquet."""

    context = {"staging_table": ctx.staging_table}

    select_sql = render_sql_template(ctx.sql_path_load, context)
    logger.info(f"Transforming {ctx.source_name} -> {ctx.output}...")

    count = execute_and_export(conn, select_sql, ctx.output)
    return count


def process_sources(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> None:
    """Process a single source."""
    try:
        count = run_transformation(conn, ctx)
        logger.info(f"SUCCESS: Created Parquet file with {count} rows.")
        log_parquet_overview(conn, ctx)
    except Exception as err:
        logger.critical("Pipeline execution failed!", exc_info=True)
        raise RuntimeError(f"Preprocessing Service Failure: {err}") from err


def run_preprocessing() -> None:
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "preprocessing")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting preprocessing-pipeline execution...")

    source_names = list(config.sql.sources.keys())
    errors = []

    db_path = str(config.paths.database)

    if not Path(db_path).exists():
        logger.error(f"Database file not found: {db_path}")
        raise FileNotFoundError(f"Database file not found: {db_path}. Run ingestion first.")

    logger.info(f"Connecting to DuckDB database at {db_path}")

    with duckdb.connect(database=db_path, read_only=True) as conn:
        for name in source_names:
            start_time = time.perf_counter()
            try:
                ctx = SourceContext.from_config(source_name=name, cfg=config)
                process_sources(conn, ctx)
            except Exception:
                logger.error(f"Failed to process source '{name}'", exc_info=True)
                errors.append(name)

            duration = time.perf_counter() - start_time
            logger.info(f"Finished '{name}' in {duration:.2f} seconds")

    if errors:
        raise RuntimeError(f"Preprocessing failed for sources: {errors}")


if __name__ == "__main__":
    run_preprocessing()
