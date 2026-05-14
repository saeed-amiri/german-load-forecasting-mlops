# services/auth/app/rbac.py
"""
A reusable permission checker
Admin-only and user-only protected routes
"""

from typing import Callable

from fastapi import Depends, HTTPException

from .auth_dependency import get_current_user


def require_role(required_role: str) -> Callable:
    """Return a dependency function that enforces one specific role."""

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

        if user_role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return user

    return role_checker
