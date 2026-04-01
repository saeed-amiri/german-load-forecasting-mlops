"""Typed configuration for the auth service."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class AuthConfig(BaseModel):
    """Settings and runtime parameters for authentication service."""

    model_config = ConfigDict(frozen=True)

    database: Path
    init_sql: Path
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
