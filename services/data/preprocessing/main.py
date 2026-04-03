# services/data/preprocessing/main.py
"""
Build feature parquet outputs from staging tables.

The module runs source-by-source preprocessing by rendering SQL templates,
exporting query results to parquet, and logging a compact quality overview for
each generated file.
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
    """
    Log one-row quality summary for a generated parquet output.

    The summary query is read from the source log template and executed against
    the output parquet file path.
    """

    context = {"target_table": f"'{ctx.output}'"}

    sql_query = render_sql_template(ctx.sql_path_log, context)
    clean_sql = sql_query.strip().rstrip(";")
    stats_df = conn.execute(clean_sql).fetchdf()

    if not stats_df.empty:
        report = stats_df.iloc[0].to_markdown()
        logger.info(f"\n--- Features Overview ({ctx.source_name}) ---\n{report}")
    else:
        logger.warning("Features Overview returned no data.")


def run_transformation(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> int:
    """
    Render the load template and export its result set to parquet.

    Returns:
        Number of rows written to the parquet output.
    """

    context = {"staging_table": ctx.staging_table}

    select_sql = render_sql_template(ctx.sql_path_load, context)
    logger.info(f"Transforming {ctx.source_name} -> {ctx.output}...")

    count = execute_and_export(conn, select_sql, ctx.output)
    return count


def process_sources(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> None:
    """
    Run transformation and overview logging for one source.

    Raises:
        RuntimeError: If preprocessing fails for the current source.
    """
    try:
        count = run_transformation(conn, ctx)
        logger.info(f"SUCCESS: Created Parquet file with {count} rows.")
        log_parquet_overview(conn, ctx)
    except Exception as err:
        raise RuntimeError(f"Preprocessing failed for source '{ctx.source_name}'") from err


def run_preprocessing() -> None:
    """
    Execute preprocessing for all configured sources.

    The function initializes config and logging, validates that ingestion output
    database exists, processes each source independently, and raises a summary
    error if any source fails.
    """
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "preprocessing")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting preprocessing-pipeline execution...")

    source_names = list(config.sql.sources.keys())
    errors: list[str] = []

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
            except Exception as err:
                logger.error("Failed to process source '%s': %s", name, err, exc_info=True)
                errors.append(name)

            duration = time.perf_counter() - start_time
            logger.info(f"Finished '{name}' in {duration:.2f} seconds")

    if errors:
        raise RuntimeError(f"Preprocessing failed for sources: {errors}")


if __name__ == "__main__":
    run_preprocessing()
