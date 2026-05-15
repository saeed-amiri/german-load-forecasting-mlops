# services/auth/app/rbac.py
"""
Role-based access control: role matrix definition and reusable permission checkers.

Role hierarchy (highest to lowest): admin > engineer > ops > viewer
Admin always passes every role check.
"""

from typing import Callable

from fastapi import Depends, HTTPException

from .auth_dependency import get_current_user

# ---------------------------------------------------------------------------
# Role Matrix
# Maps each nginx-proxied service path prefix to the set of roles allowed.
# ---------------------------------------------------------------------------
ROLE_MATRIX: dict[str, set[str]] = {
    "/api/":        {"admin", "engineer", "viewer"},
    "/auth/":       {"admin", "engineer", "viewer"},
    "/airflow/":    {"admin", "engineer"},
    "/mlflow/":     {"admin", "engineer"},
    "/grafana/":    {"admin", "engineer", "ops", "viewer"},
    "/prometheus/": {"admin", "ops"},
    "/alerts/":     {"admin", "ops"},
    "/cadvisor/":   {"admin", "ops"},
    "/node/":       {"admin", "ops"},
}

# Admin bypasses every role check.
ADMIN_ROLE = "admin"


def require_role(*allowed_roles: str) -> Callable:
    """
    Return a FastAPI dependency that passes when the current user holds
    at least one of ``allowed_roles``.  Admin always passes regardless.

    Usage:
        @router.get("/airflow-data")
        def route(user=Depends(require_role("engineer", "admin"))):
            ...
    """
    role_set = set(allowed_roles)

    def role_checker(user=Depends(get_current_user)):
        """Check the authenticated user's role against the required role.

        Args:
            user: Decoded JWT payload injected by ``get_current_user``.

        Returns:
            The user payload if the role matches.

        Raises:
            HTTPException: 403 if the user's role does not match ``required_role``.
        """
        user_role = user.get("role")

        if user_role == ADMIN_ROLE or user_role in role_set:
            return user

        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return role_checker


def require_service_access(service_path: str) -> Callable:
    """
    Return a FastAPI dependency that enforces access based on ROLE_MATRIX.

    ``service_path`` should match a key in ROLE_MATRIX, e.g. ``"/mlflow/"``.
    """
    allowed = ROLE_MATRIX.get(service_path, set())

    def role_checker(user=Depends(get_current_user)):
        user_role = user.get("role")

        if user_role == ADMIN_ROLE or user_role in allowed:
            return user

        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return role_checker
