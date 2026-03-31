# services/auth/tests/test_register.py

from fastapi.testclient import TestClient

from services.auth.app.database import init_db
from services.auth.app.main import app

client = TestClient(app)


def setup_module(module):
    init_db()


def test_register_success():
    response = client.post("/auth/register", json={"username": "newuser", "password": "mypassword", "role": "admin"})

    assert response.status_code == 200
    data = response.json()

    assert data["username"] == "newuser"
    assert data["role"] == "admin"
    assert "access_token" in data


def test_register_duplicate_user():
    # First registration
    client.post("/auth/register", json={"username": "duplicate", "password": "pw"})

    # Second registration should fail
    response = client.post("/auth/register", json={"username": "duplicate", "password": "pw"})

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"
