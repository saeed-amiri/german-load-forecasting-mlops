# services/auth/app/routers/register.py
"""Handles user registration via POST /auth/register.

Hashes the submitted password, persists the new user in DuckDB, and returns
a JWT access token so the client is immediately authenticated after sign-up.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..app.database import create_user
from ..app.hashing import hash_password
from ..app.jwt_utils import create_access_token

router = APIRouter()


class RegisterRequest(BaseModel):
    """Request body for the /auth/register endpoint.

    Attributes:
        username: Desired unique login name.
        password: Plain-text password — hashed server-side before storage.
        role: Access role to assign. Defaults to ``"user"``.
    """

    username: str
    password: str
    role: str = "user"


@router.post("/register")
def register(data: RegisterRequest):
    """Register a new user and return a bearer token.

    Args:
        data: Parsed ``RegisterRequest`` body containing username, password, and role.

    Returns:
        JSON with ``access_token``, ``token_type``, ``username``, ``role``,
        and a success message.

    Raises:
        HTTPException: 400 if a user with the same username already exists.
    """
    hashed = hash_password(data.password)
    user = create_user(data.username, hashed, data.role)

    if not user:
        raise HTTPException(status_code=400, detail="User already exists")

    token = create_access_token({"sub": user.username, "role": user.role})
    return {
        "message": "User created successfully",
        "username": user.username,
        "role": user.role,
        "access_token": token,
        "token_type": "bearer",
    }
