# services/auth/app/main.py
"""Bootstraps the FastAPI app and registers all authentication routes.
## Auth Service — Overview
It's a **standalone FastAPI microservice** that handles identity and access management for the MLOps
pipeline.

Built with these layers:

### Core Responsibilities

1. **User Registration** (`POST /auth/register`)  
   Accepts username/password/role, hashes the password (bcrypt), stores the user in a **DuckDB**
   database, and immediately returns a JWT token.

2. **Login** (`POST /auth/login`)  
   Verifies credentials against the DB, and returns a signed **JWT bearer token** with the user's
   identity and role embedded.

3. **JWT Protection** (`GET /auth/protected`)  
   A demo/utility route showing how any route can be guarded — validates the Bearer token and returns
   the decoded payload.

4. **RBAC (Role-Based Access Control)**  
   - `GET /auth/admin-only` — only `admin` role allowed  
   - `GET /auth/user-only` — only `user` role allowed  
   - Enforced via a reusable `require_role()` dependency factory

### Architecture Decisions

| Concern | Choice |
|---|---|
| Framework | FastAPI |
| Database | DuckDB (file-based, no server needed) |
| Password hashing | bcrypt (via `hashing.py`) |
| Token format | JWT (via `python-jose`) |
| Config | Loaded from `PipelineConfig` (YAML), cached with `lru_cache` |

### The idea behind it
It's a **lightweight auth sidecar** for the ML pipeline — not a full identity provider.
It gives other services (Airflow DAGs, model-serving APIs, etc.) a simple way to gate endpoints
behind JWT-authenticated roles (`admin` vs `user`), using a local DuckDB file instead of a full
PostgreSQL/Redis stack. Keeps infrastructure minimal while still supporting RBAC.
"""

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
