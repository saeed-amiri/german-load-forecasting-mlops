# services/auth/app/auth_dependency.py
"""FastAPI dependency for protecting routes with JWT bearer tokens.

Extracts the ``Authorization: Bearer <token>`` header, validates the JWT,
and returns the decoded payload so route handlers can access the caller's
identity and role without repeating token-verification logic everywhere.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_utils import decode_access_token

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Validate the bearer token and return the decoded JWT payload.

    Intended to be used as a FastAPI ``Depends`` on any protected route.

    Args:
        credentials: Bearer credentials extracted from the ``Authorization`` header
            by ``HTTPBearer``.

    Returns:
        The decoded JWT payload dict (contains at minimum ``sub`` and ``role``).

    Raises:
        HTTPException: 401 if the token is missing, invalid, or expired.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload
