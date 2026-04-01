# services/auth/app/routes/rbac_test.py

from fastapi import APIRouter, Depends

from ..app.rbac import require_role

router = APIRouter()


@router.get("/admin-only")
def admin_only_route(user=Depends(require_role("admin"))):
    return {"message": "Welcome admin", "user": user}


@router.get("/user-only")
def user_only_route(user=Depends(require_role("user"))):
    return {"message": "Welcome user", "user": user}
