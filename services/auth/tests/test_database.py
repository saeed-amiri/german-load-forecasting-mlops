# services/auth/tests/test_database.py

from uuid import uuid4

from services.auth.app.database import (
    create_user,
    get_user,
    init_db,
    user_exists,
)
from services.auth.app.hashing import hash_password


def test_create_and_get_user():
    init_db()
    username = f"alice-{uuid4().hex[:8]}"
    pw_hash = hash_password("mypassword")
    created = create_user(username, pw_hash, "admin")

    assert created is not None
    assert created.username == username

    fetched = get_user(username)

    assert fetched is not None
    assert fetched.username == username
    assert fetched.role == "admin"
    assert fetched.password_hashed == pw_hash


def test_get_missing_user():
    init_db()
    assert get_user("does_not_exist") is None


def test_user_exists():
    init_db()
    create_user("alice", hash_password("pw"))
    assert user_exists("alice") is True


def test_user_does_not_exist():
    init_db()
    assert user_exists("ghost") is False
