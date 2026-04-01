# services/auth/tests/test_rbac.py

from fastapi.testclient import TestClient

from services.auth.app.jwt_utils import create_access_token
from services.auth.app.main import app

client = TestClient(app)


def test_admin_access():
    token = create_access_token({"sub": "alice", "role": "admin"})

    response = client.get("/auth/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "Welcome admin"


def test_admin_access_denied_for_user():
    token = create_access_token({"sub": "bob", "role": "user"})

    response = client.get("/auth/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_user_access():
    token = create_access_token({"sub": "bob", "role": "user"})

    response = client.get("/auth/user-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "Welcome user"


def test_user_access_denied_for_admin():
    token = create_access_token({"sub": "alice", "role": "admin"})

    response = client.get("/auth/user-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
