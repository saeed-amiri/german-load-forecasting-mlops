# services/auth/app/routes/protected.py

from fastapi import APIRouter, Depends

from services.auth.app.auth_dependency import get_current_user

router = APIRouter()


@router.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "Access granted", "user": user}
