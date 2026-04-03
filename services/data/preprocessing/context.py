"""
Build preprocessing source context from pipeline configuration.

Each context bundles SQL templates and output location needed to transform a
staging table into feature parquet for a source.
"""

from dataclasses import dataclass
from pathlib import Path

from configs.config_sql import sql_script_path
from configs.main import PipelineConfig


@dataclass
class SourceContext:
    """Resolved preprocessing inputs and output paths for one source."""

    source_name: str
    sql_path_load: Path
    sql_path_log: Path
    staging_table: str
    output: Path

    @classmethod
    def from_config(cls, source_name: str, cfg: PipelineConfig) -> SourceContext:
        """
        Create preprocessing context for a configured source.

        Resolves load/log SQL template paths, staging table name, and parquet
        destination while validating required configuration sections.
        """
        source_cfg = cfg.sql.sources.get(source_name)
        if not source_cfg:
            raise ValueError(f"Source {source_name} not found")

        if cfg.runtime is None:
            raise RuntimeError("Runtime configuration is not initialized.")

        sql_path_load = sql_script_path(
            source_cfg.features.sql_files.load,
            cfg.runtime.sql_dir,
        )
        sql_path_log = sql_script_path(
            source_cfg.features.sql_files.log,
            cfg.runtime.sql_dir,
        )
        output = cfg.paths.processed_file
        return cls(
            source_name=source_name,
            sql_path_load=sql_path_load,
            sql_path_log=sql_path_log,
            staging_table=source_cfg.staging.tables.main,
            output=output,
        )
