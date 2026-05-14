# services/auth/app/routes/protected.py
"""Provides a token-gated smoke-test endpoint at GET /auth/protected.

Used to verify that a bearer token is valid and to inspect the decoded payload
(username, role) without performing any business logic.
"""

from fastapi import APIRouter, Depends

from services.auth.app.auth_dependency import get_current_user

router = APIRouter()


@router.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    """Return the caller's decoded token payload as proof of authentication.

    Args:
        user: Decoded JWT payload injected by ``get_current_user``.

    Returns:
        JSON with ``message`` and the full ``user`` payload dict.
    """
    return {"message": "Access granted", "user": user}
