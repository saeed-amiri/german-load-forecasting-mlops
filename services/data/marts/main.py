# services/data/marts/main.py
"""
Marts Service.
Responsible for creating aggregated tables (Data Marts) for consumption by the API.
Dependencies: Preprocessing Service (must run first).
"""

import logging
import time
from pathlib import Path

import duckdb

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging
from core.sql_helpers import render_sql_template

from .context import SourceContext

logger = logging.getLogger(__name__)


def _export_table(conn: duckdb.DuckDBPyConnection, table_name: str, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    conn.execute(f"COPY {table_name} TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    count_row = conn.execute(f"SELECT COUNT(*) FROM '{output_path}'").fetchone()
    return count_row[0] if count_row else 0


def _process_source(conn: duckdb.DuckDBPyConnection, ctx: SourceContext) -> None:
    temp_main = f"tmp_marts_{ctx.source_name}"
    temp_melt = f"tmp_melt_{ctx.source_name}"

    features_source = f"'{ctx.features_parquet}'"

    context_main = {
        "features_table": features_source,
        "marts_table": temp_main,
    }
    sql_main = render_sql_template(ctx.sql_path_main, context_main)
    conn.execute(sql_main)
    main_count = _export_table(conn, temp_main, ctx.output_main_parquet)

    context_melt = {
        "features_table": features_source,
        "load_melt": temp_melt,
    }
    sql_melt = render_sql_template(ctx.sql_path_melt, context_melt)
    conn.execute(sql_melt)
    melt_count = _export_table(conn, temp_melt, ctx.output_melt_parquet)

    logger.info(
        "SUCCESS: Source '%s' marts exported | main: %s (%s rows) | melt: %s (%s rows)",
        ctx.source_name,
        ctx.output_main_parquet,
        main_count,
        ctx.output_melt_parquet,
        melt_count,
    )


def run_marts_pipeline() -> None:
    """Entry point for the marts pipeline."""
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "marts")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting Marts pipeline execution...")

    source_names = list(config.sql.sources.keys())
    errors: list[str] = []

    if not config.paths.processed_file.exists():
        raise FileNotFoundError(
            f"Processed parquet not found: {config.paths.processed_file}. Run preprocessing first."
        )

    with duckdb.connect() as conn:
        for source_name in source_names:
            start_time = time.perf_counter()
            try:
                ctx = SourceContext.from_config(source_name=source_name, cfg=config)
                _process_source(conn, ctx)
            except Exception:
                logger.error("Failed to build marts for source '%s'", source_name, exc_info=True)
                errors.append(source_name)

            duration = time.perf_counter() - start_time
            logger.info("Finished '%s' in %.2f seconds", source_name, duration)

    if errors:
        raise RuntimeError(f"Marts pipeline failed for sources: {errors}")


if __name__ == "__main__":
    run_marts_pipeline()
