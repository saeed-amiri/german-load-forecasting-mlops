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
from .database import create_table_from_csv, execute_sql

logger = logging.getLogger(__name__)


def process_source(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> None:
    """load and dump the data into a daatbase"""
    try:
        logger.info(f"Processing source: {ctx.source_name}")

        raw_table = f"raw_{ctx.source_name}"
        staging_table = ctx.staging_table

        logger.info(f"Loading full CSV into raw table '{raw_table}'...")
        create_table_from_csv(conn, raw_table, csv_path=ctx.raw_file)

        with open(ctx.sql_template_path, "r", encoding="utf8") as f:
            template = Template(f.read())

        columns_dict = {col.clean: col for col in ctx.columns}
        sql_query = template.render(
            raw_source_table=raw_table,
            staging_table=staging_table,
            columns=ctx.columns,
            colmap=columns_dict,
        )

        logger.info("Executing staging transformation...")
        execute_sql(conn, sql_query)

        logger.info(f"SUCCESS: Source '{ctx.source_name}' processed.")

    except Exception as err:
        logger.error("Failed")
        raise RuntimeError(f"Processing {ctx.raw_file} Failed!") from err


def run_ingestion() -> None:
    """
    Main entry point for ingestion.
    """
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
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
