# services/auth/app/routes/rbac_test.py
"""Test endpoints for verifying role-based access control (RBAC).

Exposes two role-restricted routes used during development and integration
testing to confirm that the ``require_role`` dependency correctly enforces
``"admin"`` and ``"user"`` role boundaries.
"""

from fastapi import APIRouter, Depends

from ..app.rbac import require_role, require_service_access

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
def user_only_route(user=Depends(require_role("viewer"))):
    """Endpoint accessible only to users with the ``"viewer"`` role.

    Args:
        user: Decoded JWT payload, injected and role-checked by ``require_role``.

    Returns:
        A welcome message and the user payload.

    Raises:
        HTTPException: 403 if the caller's role is not ``"viewer"``.
    """
    return {"message": "Welcome user", "user": user}


@router.get("/airflow-access")
def airflow_access_route(user=Depends(require_service_access("/airflow/"))):
    return {"message": "Airflow access granted", "user": user}


@router.get("/mlflow-access")
def mlflow_access_route(user=Depends(require_service_access("/mlflow/"))):
    return {"message": "MLflow access granted", "user": user}
