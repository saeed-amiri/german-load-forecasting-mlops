# services/auth/context.py
"""Runtime configuration context for the auth service.

``AuthContext`` is an immutable dataclass that bundles every piece of
configuration the auth service needs (DB path, JWT settings, SQL asset
path). A single cached instance is created at startup via
``get_auth_context()`` and shared across all modules, avoiding repeated
config-file reads and making the service easy to test by injecting a
custom context.
"""
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
        """Build an ``AuthContext`` from a loaded ``PipelineConfig``.

        Args:
            cfg: Fully parsed pipeline configuration object.

        Returns:
            A frozen ``AuthContext`` populated from ``cfg.auth``.
        """
        return cls(
            database_path=cfg.auth.database,
            init_sql_path=cfg.auth.init_sql,
            jwt_secret_key=cfg.auth.jwt_secret_key,
            jwt_algorithm=cfg.auth.jwt_algorithm,
            access_token_expire_minutes=cfg.auth.access_token_expire_minutes,
        )


@lru_cache(maxsize=1)
def get_auth_context(start_file: Path | None = None) -> AuthContext:
    """Return the singleton ``AuthContext``, loading config on first call.

    Results are cached via ``lru_cache`` so the config file is only read once
    per process. Pass ``start_file=Path(__file__)`` from inside a package to
    let ``load_config`` resolve relative paths correctly.

    Args:
        start_file: Optional path hint used by ``load_config`` to locate the
            config directory relative to the caller. Defaults to None.

    Returns:
        The shared ``AuthContext`` instance for this process.
    """
    cfg: PipelineConfig = load_config(config_name="config", start_file=start_file)
    return AuthContext.from_config(cfg)
