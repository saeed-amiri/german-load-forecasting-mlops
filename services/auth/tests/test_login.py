# services/auth/tests/test_test_login.py

from fastapi.testclient import TestClient

from services.auth.app.database import create_user, init_db
from services.auth.app.hashing import hash_password
from services.auth.app.main import app

client = TestClient(app)


def setup_module(module):
    init_db()
    create_user("alice", hash_password("mypassword"), "admin")


def test_login_success():
    response = client.post("/auth/login", json={"username": "alice", "password": "mypassword"})

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["username"] == "alice"
    assert data["role"] == "admin"


def test_login_wrong_password():
    response = client.post("/auth/login", json={"username": "alice", "password": "wrong"})

    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post("/auth/login", json={"username": "ghost", "password": "whatever"})

    assert response.status_code == 401
