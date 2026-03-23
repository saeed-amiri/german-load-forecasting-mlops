# services/data/ingestion/main.py

import logging
from pathlib import Path

from jinja2 import Template

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from .context import SourceContext
from .io_helpers import drop_table, execute_sql_script, write_csv_to_table

logger = logging.getLogger(__name__)


def process_source(ctx: SourceContext):
    """
    Pure business logic for processing ONE source.
    This function knows nothing about the global config.
    """
    logger.info(f"Processing source: {ctx.source_name}")

    logger.info(f"Loading CSV into raw table '{ctx.raw_table}'...")
    write_csv_to_table(
        csv_path=ctx.raw_file,
        database_path=ctx.database,
        table_name=ctx.raw_table,
    )

    with open(ctx.sql_template_path, "r", encoding="utf8") as f:
        template = Template(f.read())

    columns_dict = {col.clean: col for col in ctx.columns}

    sql_query = template.render(
        raw_source_table=ctx.raw_table,
        staging_table=ctx.staging_table,
        columns=ctx.columns,
        colmap=columns_dict,
    )

    logger.info("Executing staging transformation...")
    execute_sql_script(ctx.database, sql_query)

    logger.info(f"Dropping temporary table '{ctx.raw_table}'...")
    drop_table(ctx.database, ctx.raw_table)


def run_ingestion() -> None:
    """
    Main entry point for ingestion.
    """

    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "ingestion")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    source_names = config.sql.sources.keys()

    logger.info("Starting ingestion-pipeline execution...")

    errors = []

    for name in source_names:
        try:
            ctx = SourceContext.from_config(name, config)

            process_source(ctx)

            logger.info(f"SUCCESS: Source '{name}' processed.")

        except Exception as err:
            logger.error(f"Failed to process source '{name}'", exc_info=True)
            errors.append((name, err))

    if errors:
        raise RuntimeError(f"Ingestion failed for sources: {errors}")


if __name__ == "__main__":
    run_ingestion()
