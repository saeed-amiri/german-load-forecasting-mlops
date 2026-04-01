from pathlib import Path

import pytest

from services.auth.app.database import init_db
from services.auth.context import AuthContext

TEST_DB = Path("test_auth.duckdb")
INIT_SQL = Path("sql/auth/user.sql")


@pytest.fixture(autouse=True)
def isolated_auth_context(monkeypatch):
    # Keep DB/user seeding inside pytest fixtures or test bodies.
    # Avoid setup_module/setup_class seeding because those run outside
    # this autouse fixture lifecycle and bypass monkeypatched auth context.
    ctx = AuthContext(
        database_path=TEST_DB,
        init_sql_path=INIT_SQL,
        jwt_secret_key="test-secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=5,
    )

    monkeypatch.setattr("services.auth.app.database.get_auth_context", lambda: ctx)
    monkeypatch.setattr("services.auth.app.jwt_utils.get_auth_context", lambda: ctx)
    monkeypatch.setattr("services.auth.app.main.auth_ctx", ctx, raising=False)
    monkeypatch.setattr("services.auth.app.main.app.state.auth_ctx", ctx, raising=False)

    init_db(ctx)

    yield ctx
