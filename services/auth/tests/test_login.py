# services/auth/tests/test_test_login.py

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from services.auth.app.database import create_user, init_db
from services.auth.app.hashing import hash_password
from services.auth.app.main import app

client = TestClient(app)


@pytest.fixture()
def seeded_user() -> tuple[str, str]:
    username = f"alice-{uuid4().hex[:8]}"
    password = "mypassword"
    init_db()
    create_user(username, hash_password(password), "admin")
    return username, password


def test_login_success(seeded_user: tuple[str, str]):
    username, password = seeded_user
    response = client.post("/auth/login", json={"username": username, "password": password})

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["username"] == username
    assert data["role"] == "admin"


def test_login_wrong_password(seeded_user: tuple[str, str]):
    username, _ = seeded_user
    response = client.post("/auth/login", json={"username": username, "password": "wrong"})

    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post("/auth/login", json={"username": "ghost", "password": "whatever"})

    assert response.status_code == 401
