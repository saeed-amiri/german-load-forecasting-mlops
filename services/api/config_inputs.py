"""
Utilities for loading YAML config inputs for API template rendering.

This module is intentionally focused on presentation-facing config data:
- reading `configs/inputs/*.yml`
- masking sensitive values before sending to templates
- providing page-level header fields from the `api.ui` section
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_SENSITIVE_TOKENS = ("secret", "password", "token", "key")


def _mask_sensitive(value: Any) -> Any:
    """Recursively mask sensitive dictionary keys in a nested structure.

    Args:
        value: Any YAML-derived object (dict, list, scalar).

    Returns:
        A copy of the input structure where values under keys containing
        sensitive tokens (for example `secret`, `token`, `password`, `key`)
        are replaced with `"***"`.
    """
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for k, v in value.items():
            if any(token in k.lower() for token in _SENSITIVE_TOKENS):
                masked[k] = "***"
            else:
                masked[k] = _mask_sensitive(v)
        return masked
    if isinstance(value, list):
        return [_mask_sensitive(item) for item in value]
    return value


@lru_cache(maxsize=32)
def _load_config_inputs_cached(inputs_dir: str, signature: tuple[tuple[str, int, int], ...]) -> dict[str, Any]:
    """Load YAML input files with cache keyed by a filesystem signature.

    Args:
        inputs_dir: Absolute or relative path to the `configs/inputs` directory.
        signature: Tuple capturing each file name and metadata needed for
            cache invalidation.

    Returns:
        Mapping of YAML stem name to masked YAML content.
    """
    root = Path(inputs_dir)
    if not root.exists() or not root.is_dir():
        return {}

    loaded: dict[str, Any] = {}
    for file_path in sorted(root.glob("*.yml")):
        data = yaml.safe_load(file_path.read_text()) or {}
        loaded[file_path.stem] = _mask_sensitive(data)

    return loaded


def _signature_for_inputs(root: Path) -> tuple[tuple[str, int, int], ...]:
    """Build an immutable signature for all YAML files in an inputs folder.

    The signature combines file name, modification timestamp, and size so
    template-facing config can refresh automatically when files change.

    Args:
        root: Directory containing YAML config inputs.

    Returns:
        Tuple usable as a cache key component.
    """
    if not root.exists() or not root.is_dir():
        return ()

    signature: list[tuple[str, int, int]] = []
    for file_path in sorted(root.glob("*.yml")):
        stat = file_path.stat()
        signature.append((file_path.name, stat.st_mtime_ns, stat.st_size))
    return tuple(signature)


def load_config_inputs(inputs_dir: str) -> dict[str, Any]:
    """Load masked YAML input files with automatic cache invalidation.

    Args:
        inputs_dir: Path to the directory holding `*.yml` config inputs.

    Returns:
        Mapping from file stem (for example `api`) to masked YAML data.
    """
    root = Path(inputs_dir)
    signature = _signature_for_inputs(root)
    return _load_config_inputs_cached(str(root), signature)


def page_header_from_inputs(config_inputs: dict[str, Any], page_key: str) -> dict[str, Any]:
    """Extract header title/subtitle/tabs for a given page from config inputs.

    Reads values from `config_inputs["api"]["ui"][page_key]` and falls back
    to safe defaults when fields are missing.

    Args:
        config_inputs: Aggregated YAML inputs previously loaded by
            `load_config_inputs`.
        page_key: Page identifier, usually `index` or `data`.

    Returns:
        Dictionary containing `header_title`, `header_subtitle`, and
        `header_tabs` for template rendering.
    """
    api_cfg = config_inputs.get("api", {}) if isinstance(config_inputs.get("api", {}), dict) else {}
    ui_cfg = api_cfg.get("ui", {}) if isinstance(api_cfg.get("ui", {}), dict) else {}
    page_cfg = ui_cfg.get(page_key, {}) if isinstance(ui_cfg.get(page_key, {}), dict) else {}

    defaults = {
        "index": {
            "header_title": "Electricity: German Load Forecating",
            "header_subtitle": "Welcome to the MLOps Platform.",
            "header_tabs": [],
        },
        "data": {
            "header_title": "Load Analysis",
            "header_subtitle": "Explore forecasts, features, and historical demand.",
            "header_tabs": [],
        },
    }

    base = defaults.get(page_key, {"header_title": "", "header_subtitle": "", "header_tabs": []})
    return {
        "header_title": page_cfg.get("title", base["header_title"]),
        "header_subtitle": page_cfg.get("subtitle", base["header_subtitle"]),
        "header_tabs": page_cfg.get("tabs", base["header_tabs"]),
    }
