# services/auth/app/jwt_utils.py
"""Creates and verifies JWT tokens, embedding user identity and roles."""

from datetime import datetime, timedelta, timezone  #

from jose import JWTError, jwt

# Move to .env
SECERT_KEY: str = "super-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECERT_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode a JWT and return payload, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, SECERT_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
