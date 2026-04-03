"""
Build marts source context from pipeline configuration.

The context resolves SQL templates and parquet output destinations used to
materialize both main and melt marts datasets for each source.
"""

from dataclasses import dataclass
from pathlib import Path

from configs.config_sql import sql_script_path
from configs.main import PipelineConfig


@dataclass
class SourceContext:
    """Resolved marts SQL and output paths for one configured source."""

    source_name: str
    sql_path_main: Path
    sql_path_melt: Path
    features_parquet: Path
    output_main_parquet: Path
    output_melt_parquet: Path

    @classmethod
    def from_config(cls, source_name: str, cfg: PipelineConfig) -> "SourceContext":
        """
        Create marts context for a configured source.

        Validates source and runtime availability, resolves SQL template paths,
        and computes parquet output locations for main and melt marts outputs.
        """
        source_cfg = cfg.sql.sources.get(source_name)
        if not source_cfg:
            raise ValueError(f"Source {source_name} not found")

        if cfg.runtime is None:
            raise RuntimeError("Runtime configuration is not initialized.")

        sql_path_main = sql_script_path(source_cfg.marts.sql_files.load, cfg.runtime.sql_dir)
        sql_path_melt = sql_script_path(source_cfg.marts.sql_files.load_melt, cfg.runtime.sql_dir)

        output_main = cfg.paths.marts_dir / f"{source_cfg.marts.tables.main}.parquet"
        output_melt = cfg.paths.marts_dir / f"{source_cfg.marts.tables.melt}.parquet"

        return cls(
            source_name=source_name,
            sql_path_main=sql_path_main,
            sql_path_melt=sql_path_melt,
            features_parquet=cfg.paths.processed_file,
            output_main_parquet=output_main,
            output_melt_parquet=output_melt,
        )
