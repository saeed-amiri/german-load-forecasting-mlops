# configs/config_api.py
"""
Setting up configuration for api
It will be handle by configs/main.py
"""

from pathlib import Path
from dataclasses import dataclass, field


@dataclass(frozen=True)
class APIConfig:
    """Settings and parameters for API"""

    templates: Path


def initialize_api_config(project_root, config_dict) -> APIConfig:
    api_cfg = config_dict.get("api", {})
    api = APIConfig(templates=(project_root / api_cfg["templates"]).resolve())
    return api
