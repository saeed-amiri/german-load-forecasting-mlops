# configs/config_logs.py
"""
Setting up configuration for log files
It will be handle by configs/main.py
"""

import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LoggingConfig:
    """Logging behavior and file naming for services."""

    level: int = logging.INFO
    to_console: bool = True
    ingestion_log: str = "ingest.log"
    preprocessing_log: str = "preprocess.log"


def initialize_logging_config(config_dict):
    logging_config = config_dict.get("logging", {})
    log_cfg = LoggingConfig(
        level=_parse_log_level(logging_config.get("level", logging.INFO)),
        to_console=bool(logging_config.get("to_console", True)),
        ingestion_log=str(logging_config.get("ingestion_log", "ingest.log")),
        preprocessing_log=str(logging_config.get("preprocessing_log", "preprocess.log")),
    )

    return log_cfg


def _parse_log_level(raw_level: Any) -> int:
    if isinstance(raw_level, int):
        return raw_level
    if isinstance(raw_level, str):
        return getattr(logging, raw_level.upper(), logging.INFO)
    return logging.INFO
