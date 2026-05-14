# services/auth/app/routes/rbac_test.py
"""Test endpoints for verifying role-based access control (RBAC).

Exposes two role-restricted routes used during development and integration
testing to confirm that the ``require_role`` dependency correctly enforces
``"admin"`` and ``"user"`` role boundaries.
"""

from fastapi import APIRouter, Depends

from ..app.rbac import require_role

router = APIRouter()


@router.get("/admin-only")
def admin_only_route(user=Depends(require_role("admin"))):
    """Endpoint accessible only to users with the ``"admin"`` role.

    Args:
        user: Decoded JWT payload, injected and role-checked by ``require_role``.

    Returns:
        A welcome message and the user payload.

    Raises:
        HTTPException: 403 if the caller's role is not ``"admin"``.
    """
    return {"message": "Welcome admin", "user": user}


@router.get("/user-only")
def user_only_route(user=Depends(require_role("user"))):
    """Endpoint accessible only to users with the ``"user"`` role.

    Args:
        user: Decoded JWT payload, injected and role-checked by ``require_role``.

    Returns:
        A welcome message and the user payload.

    Raises:
        HTTPException: 403 if the caller's role is not ``"user"``.
    """
    return {"message": "Welcome user", "user": user}
