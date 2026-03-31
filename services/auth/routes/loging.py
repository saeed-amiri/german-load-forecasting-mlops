# services/auth/routers/loging.py
"""Implements the /auth/login endpoint: validates credentials and returns a JWT."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..app.database import get_user
from ..app.hashing import verify_password
from ..app.jwt_utils import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    user = get_user(data.username)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(data.password, user.password_hashed):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username, "role": user.role})

    return {
        "access_token": token,
        "token": "bearer",
        "username": user.username,
        "role": user.role,
    }
