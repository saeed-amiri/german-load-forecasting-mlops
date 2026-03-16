"""
Logging Configuration Module
============================
Provides a unified logging interface for all pipeline stages.

This module ensures consistent log formatting and dual-output
(file & console) across standalone scripts and Docker
containers.
"""

import logging
from pathlib import Path


def setup_logging(log_file: Path, level: int = logging.INFO, to_consle: bool = True) -> None:
    """
    Configures a root logger that outputs to both a file and
    the console.
    """
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # Prevent duplicate handlers if the function is called twice
    if root.handlers:
        root.handlers.clear()

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Console Handle
    if to_consle:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(fmt)
        root.addHandler(console_handler)

    logging.info("Logging initialized. Output file: %s", log_file)
