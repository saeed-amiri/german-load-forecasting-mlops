# services/auth/app/models.py
# Defines the User model (username, password_hashed, role, etc.)

from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    username: str
    password_hashed: str
    role: str
