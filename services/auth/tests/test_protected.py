# services/auth/tests/test_protected.py

from fastapi.testclient import TestClient

from services.auth.app.jwt_utils import create_access_token
from services.auth.app.main import app

client = TestClient(app)


def test_protected_route_success():
    token = create_access_token({"sub": "alice", "role": "admin"})

    response = client.get("/auth/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Access granted"
    assert data["user"]["sub"] == "alice"
    assert data["user"]["role"] == "admin"


def test_protected_route_missing_token():
    response = client.get("/auth/protected")

    assert response.status_code == 401


def test_protected_route_invalid_token():
    response = client.get("/auth/protected", headers={"Authorization": "Bearer invalidtoken123"})

    assert response.status_code == 401
