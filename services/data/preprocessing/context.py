# services/data/preprocessing/context.py

from dataclasses import dataclass
from pathlib import Path

from configs.config_sql import sql_script_path
from configs.main import PipelineConfig


@dataclass
class SourceContext:
    """Context for a single data source"""

    source_name: str
    sql_path_load: Path
    sql_path_log: Path
    staging_table: str
    output: Path

    @classmethod
    def from_config(cls, source_name: str, cfg: PipelineConfig) -> SourceContext:
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
