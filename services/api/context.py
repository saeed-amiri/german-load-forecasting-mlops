from dataclasses import dataclass
from pathlib import Path

from configs.main import PipelineConfig


@dataclass
class APIContext:
    """Runtime context for API data access and templates/static paths."""

    source_name: str
    templates_dir: Path
    static_dir: Path
    marts_main_parquet: Path
    marts_melt_parquet: Path

    @classmethod
    def from_config(cls, cfg: PipelineConfig, source_name: str | None = None) -> "APIContext":
        names = list(cfg.sql.sources.keys())
        if not names:
            raise ValueError("No sources configured in sql.sources")

        selected = source_name or names[0]
        source_cfg = cfg.sql.sources.get(selected)
        if not source_cfg:
            raise ValueError(f"Source {selected} not found")

        templates = (
            cfg.api.templates if cfg.api.templates.is_absolute() else (cfg.project_root / cfg.api.templates).resolve()
        )
        static = cfg.api.static if cfg.api.static.is_absolute() else (cfg.project_root / cfg.api.static).resolve()

        return cls(
            source_name=selected,
            templates_dir=templates,
            static_dir=static,
            marts_main_parquet=cfg.paths.marts_dir / f"{source_cfg.marts.tables.main}.parquet",
            marts_melt_parquet=cfg.paths.marts_dir / f"{source_cfg.marts.tables.melt}.parquet",
        )
