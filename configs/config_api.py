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
    static: Path
