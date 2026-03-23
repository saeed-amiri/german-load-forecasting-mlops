# services/data/ingestion/context.py

from dataclasses import dataclass
from pathlib import Path

from configs.config_sql import ColumnMapping, sql_script_path
from configs.main import PipelineConfig


@dataclass
class SourceContext:
    """Context for a single data source."""

    source_name: str
    raw_file: Path
    database: Path
    staging_table: str
    raw_table: str
    columns: list[ColumnMapping]
    sql_template_path: Path

    @classmethod
    def from_config(cls, source_name: str, cfg: PipelineConfig):
        # Navigate the deep config once
        source_cfg = cfg.sql.sources.get(source_name)
        if not source_cfg:
            raise ValueError(f"Source {source_name} not found")

        staging_table = source_cfg.staging.tables.main
        raw_table = f"raw_{staging_table}_tmp"

        # Resolve paths
        sql_path = sql_script_path(
            source_cfg.staging.sql_files.main,
            cfg.runtime.sql_dir,
        )

        return cls(
            source_name=source_name,
            raw_file=source_cfg.raw_file,
            database=cfg.paths.database,
            staging_table=staging_table,
            raw_table=raw_table,
            columns=source_cfg.columns,
            sql_template_path=sql_path,
        )
