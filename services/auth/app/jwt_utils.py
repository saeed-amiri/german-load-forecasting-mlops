# services/auth/app/jwt_utils.py
"""Creates and verifies JWT tokens, embedding user identity and roles."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from services.auth.context import AuthContext, get_auth_context


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    ctx: AuthContext | None = None,
) -> str:
    active_ctx = ctx or get_auth_context()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=active_ctx.access_token_expire_minutes)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, active_ctx.jwt_secret_key, algorithm=active_ctx.jwt_algorithm)


def decode_access_token(token: str, ctx: AuthContext | None = None) -> dict | None:
    """Decode a JWT and return payload, or None if invalid/expired."""
    active_ctx = ctx or get_auth_context()

    try:
        payload = jwt.decode(token, active_ctx.jwt_secret_key, algorithms=[active_ctx.jwt_algorithm])
        return payload
    except JWTError:
        return None
