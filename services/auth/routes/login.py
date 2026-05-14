"""Implements the /auth/login endpoint and returns a bearer token."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..app.database import get_user
from ..app.hashing import verify_password
from ..app.jwt_utils import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    """Request body for the /auth/login endpoint.

    Attributes:
        username: The user's registered login name.
        password: The plain-text password to verify against the stored hash.
    """

    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    """Authenticate a user and return a bearer token.

    Looks up the user by username, verifies the password, and issues a signed JWT.
    Both "user not found" and "wrong password" return the same 401 to avoid
    leaking whether a username exists.

    Args:
        data: Parsed ``LoginRequest`` body with username and password.

    Returns:
        JSON with ``access_token``, ``token_type``, ``username``, and ``role``.

    Raises:
        HTTPException: 401 if the credentials are invalid.
    """
    user = get_user(data.username)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(data.password, user.password_hashed):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
    }
