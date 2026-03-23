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
        source_cfg = cfg.sql.sources.get(source_name)
        if not source_cfg:
            raise ValueError(f"Source {source_name} not found")

        if cfg.runtime is None:
            raise RuntimeError("Runtime configuration is not initialized.")

        sql_path = sql_script_path(
            source_cfg.staging.sql_files.main,
            cfg.runtime.sql_dir,
        )

        staging_table = source_cfg.staging.tables.main
        raw_table = f"raw_{source_name}"

        raw_file_path = cfg.project_root / source_cfg.raw_file

        return cls(
            source_name=source_name,
            raw_file=raw_file_path,
            database=cfg.paths.database,
            staging_table=staging_table,
            raw_table=raw_table,
            columns=source_cfg.columns,
            sql_template_path=sql_path,
        )
