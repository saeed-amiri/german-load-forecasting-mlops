# services/auth/app/hashing.py

"""
Handles password hashing and verification using argon2-cffi.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plain-text password using Argon2.

    Args:
        password: The plain-text password to hash.

    Returns:
        The Argon2 hash string, safe to store in the database.
    """
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored Argon2 hash.

    Args:
        plain_password: The password submitted by the user.
        hashed_password: The Argon2 hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
