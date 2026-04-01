# services/auth/tests/test_jwt_utils.py
from datetime import timedelta

from services.auth.app.jwt_utils import (
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_token():
    data = {"sub": "alice", "role": "admin"}
    token = create_access_token(data)

    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "alice"
    assert decoded["role"] == "admin"


def test_expired_token():
    data = {"sub": "alice"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    decoded = decode_access_token(token)

    assert decoded is None


def test_invalid_signature():
    data = {"sub": "alice"}
    token = create_access_token(data)

    # Tamper with the token
    bad_token = token + "broken"

    decoded = decode_access_token(bad_token)

    assert decoded is None
