# services/auth/context.py
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from configs.main import PipelineConfig, load_config


@dataclass(frozen=True)
class AuthContext:
    """Runtime context for auth service configuration and SQL assets."""

    database_path: Path
    init_sql_path: Path
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    @classmethod
    def from_config(cls, cfg: PipelineConfig) -> "AuthContext":
        return cls(
            database_path=cfg.auth.database,
            init_sql_path=cfg.auth.init_sql,
            jwt_secret_key=cfg.auth.jwt_secret_key,
            jwt_algorithm=cfg.auth.jwt_algorithm,
            access_token_expire_minutes=cfg.auth.access_token_expire_minutes,
        )


@lru_cache(maxsize=1)
def get_auth_context(start_file: Path | None = None) -> AuthContext:
    cfg: PipelineConfig = load_config(config_name="config", start_file=start_file)
    return AuthContext.from_config(cfg)
