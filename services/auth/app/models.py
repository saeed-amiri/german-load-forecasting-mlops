# services/auth/app/models.py
"""Pydantic models used by the auth service."""

from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    username: str
    password_hashed: str
    role: str
