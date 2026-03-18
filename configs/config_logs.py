# configs/config_logs.py
"""
Setting up configuration for log files
It will be handled by configs/main.py
"""

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .config_runtime import RuntimePaths


class LoggingConfig(BaseModel):
    """Logging behavior and file naming for services."""

    model_config = ConfigDict(frozen=True, extra="allow")

    level: int = logging.INFO
    to_console: bool = True
    service_logs: dict[str, str] = Field(default_factory=dict)

    @field_validator("level", mode="before")
    @classmethod
    def _parse_level(cls, raw_level: Any) -> int:
        if isinstance(raw_level, int):
            return raw_level
        if isinstance(raw_level, str):
            return getattr(logging, raw_level.upper(), logging.INFO)
        return logging.INFO

    @model_validator(mode="before")
    @classmethod
    def _collect_service_log_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        merged = dict(data)
        service_logs = dict(merged.get("service_logs", {}))

        for key, value in data.items():
            if key.endswith("_log") and isinstance(value, str):
                service_name = key.removesuffix("_log")
                service_logs.setdefault(service_name, value)

        merged["service_logs"] = service_logs
        return merged

    def file_name_for(self, service_name: str) -> str:
        service_key = service_name.lower()
        return self.service_logs.get(service_key, f"{service_key}.log")


def initialize_logging_config(config_dict: dict[str, Any]) -> LoggingConfig:
    logging_config = config_dict.get("logging", {}) or {}
    log_cfg = LoggingConfig.model_validate(logging_config)
    return log_cfg


def resolve_service_log_path(logging_cfg: LoggingConfig, runtime_cfg: RuntimePaths, service_name: str) -> Path:
    return runtime_cfg.logs_dir / logging_cfg.file_name_for(service_name)
