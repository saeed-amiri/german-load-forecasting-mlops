# services/auth/tests/test_database.py

from pathlib import Path

import pytest

from services.auth.app.database import (
    create_user,
    get_user,
    init_db,
    user_exists,
)
from services.auth.app.hashing import hash_password

TEST_DB = Path("test_auth.duckdb")


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    # Override DB path for tests
    monkeypatch.setattr("services.auth.app.database.DB_PATH", TEST_DB, raising=False)

    # Initialize test DB
    init_db()
    yield

    # Cleanup
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_create_and_get_user():
    pw_hash = hash_password("mypassword")
    create_user("alice", pw_hash, "admin")

    fetched = get_user("alice")

    assert fetched is not None
    assert fetched.username == "alice"
    assert fetched.role == "admin"
    assert fetched.password_hashed == pw_hash


def test_get_missing_user():
    assert get_user("does_not_exist") is None


def test_user_exists():
    init_db()
    create_user("alice", hash_password("pw"))
    assert user_exists("alice") is True


def test_user_does_not_exist():
    init_db()
    assert user_exists("ghost") is False
