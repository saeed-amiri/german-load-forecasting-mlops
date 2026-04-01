# services/auth/app/main.py
"""Bootstraps the FastAPI app and registers all authentication routes."""

from fastapi import FastAPI

from ..routes.loging import router as login_router
from ..routes.protected import router as protected_router
from ..routes.register import router as register_router
from ..routes.test_rbac import router as rbac_router

app = FastAPI()

app.include_router(login_router, prefix="/auth")
app.include_router(register_router, prefix="/auth")
app.include_router(protected_router, prefix="/auth")
app.include_router(rbac_router, prefix="/auth")
