# services/auth/app/models.py
"""Pydantic models used by the auth service."""

from pydantic import BaseModel


class User(BaseModel):
    """Represents a registered user in the auth system.

    Attributes:
        id: Auto-assigned integer primary key from DuckDB. None before insertion.
        username: Unique login name for the user.
        password_hashed: Argon2 hash of the user's password — never store plain text.
        role: Access role (e.g. ``"admin"`` or ``"user"``) used for RBAC checks.
    """

    id: int | None = None
    username: str
    password_hashed: str
    role: str
