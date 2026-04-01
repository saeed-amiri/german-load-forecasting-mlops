# services/auth/app/main.py
"""Bootstraps the FastAPI app and registers all authentication routes."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from services.auth.context import AuthContext, get_auth_context

from ..routes.login import router as login_router
from ..routes.protected import router as protected_router
from ..routes.register import router as register_router
from ..routes.test_rbac import router as rbac_router
from .database import init_db

auth_ctx: AuthContext = get_auth_context(start_file=Path(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(auth_ctx)
    yield


app = FastAPI(lifespan=lifespan)
app.state.auth_ctx = auth_ctx

app.include_router(login_router, prefix="/auth")
app.include_router(register_router, prefix="/auth")
app.include_router(protected_router, prefix="/auth")
app.include_router(rbac_router, prefix="/auth")
