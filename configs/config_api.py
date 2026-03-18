# configs/config_api.py
"""
Setting up configuration for api
It will be handle by configs/main.py
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class APIConfig(BaseModel):
    """Settings and parameters for API"""

    model_config = ConfigDict(frozen=True)

    templates: Path


def initialize_api_config(project_root: Path, config_dict: dict) -> APIConfig:
    api_cfg = config_dict.get("api", {})
    api = APIConfig(templates=(project_root / api_cfg["templates"]).resolve())
    return api
