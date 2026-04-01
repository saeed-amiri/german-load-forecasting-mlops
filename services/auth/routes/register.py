# services/auth/app/routers/register.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..app.database import create_user
from ..app.hashing import hash_password
from ..app.jwt_utils import create_access_token

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


@router.post("/register")
def register(data: RegisterRequest):
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
