# services/auth/tests/test_hashing.py

from services.auth.app.hashing import hash_password, verify_password


def test_hash_password_produce_different_hashes():
    pw = "secret123"
    h1 = hash_password(pw)
    h2 = hash_password(pw)
    assert h1 != h2


def test_verify_password_success():
    pw = "mypassword"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True


def test_verify_password_failure():
    pw = "mypassword"
    hashed = hash_password(pw)
    assert verify_password("wrong", hashed) is False
