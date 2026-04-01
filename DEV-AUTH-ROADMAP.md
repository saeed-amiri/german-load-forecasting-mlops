# Auth Roadmap and Reusable Cheat Sheet

This document explains how auth is built in this repository and gives a reusable path for future projects.

## 1) Current Architecture At A Glance

Auth is split into 6 layers:

1. Configuration layer
- Source of truth: configs/inputs/auth.yml
- Typed schema: configs/config_auth.py
- Loaded through central config: configs/main.py

2. Runtime context layer
- Context object: services/auth/context.py
- Purpose: resolve DB path, SQL path, JWT settings once and reuse everywhere

3. Persistence layer
- SQL schema: sql/auth/user.sql
- DB helper functions: services/auth/app/database.py

4. Crypto and token layer
- Password hashing: services/auth/app/hashing.py
- JWT create/decode: services/auth/app/jwt_utils.py

5. Dependency and authorization layer
- Current user dependency: services/auth/app/auth_dependency.py
- Role checks: services/auth/app/rbac.py

6. Transport layer
- FastAPI app: services/auth/app/main.py
- Routes: services/auth/routes/login.py, services/auth/routes/register.py, services/auth/routes/protected.py, services/auth/routes/test_rbac.py
- Nginx reverse proxy path: deployment/nginx/nginx.conf
- Compose service wiring: docker-compose.yml

## 2) Request Flow (Mental Model)

### Register
1. Client calls POST /auth/register.
2. Route validates payload.
3. Password is hashed with Argon2.
4. User row inserted into DuckDB.
5. JWT token returned with sub and role claims.

### Login
1. Client calls POST /auth/login.
2. Route loads user by username.
3. Password is verified against hash.
4. JWT token returned.

### Protected endpoint
1. Client sends Authorization: Bearer <token>.
2. Dependency decodes token.
3. If valid, endpoint receives payload.
4. Optional RBAC dependency enforces role.

## 3) Core Files You Should Always Have

Required auth files in a clean project:

1. Config
- configs/config_auth.py
- configs/inputs/auth.yml
- config template entry in configs/config.yml
- loader wiring in configs/config_utils.py and configs/main.py

2. Context
- services/auth/context.py

3. SQL and DB
- sql/auth/user.sql
- services/auth/app/database.py

4. Security
- services/auth/app/hashing.py
- services/auth/app/jwt_utils.py
- services/auth/app/auth_dependency.py
- services/auth/app/rbac.py

5. API
- services/auth/app/main.py
- services/auth/routes/login.py
- services/auth/routes/register.py
- services/auth/routes/protected.py

6. Deployment
- docker/auth/Dockerfile
- docker/auth/requirements.txt
- docker-compose.yml service entry
- deployment/nginx/nginx.conf route for /auth/

## 4) Reusable Implementation Checklist

Use this list when implementing auth in another project:

1. Define typed auth config and connect it to global config loading.
2. Create AuthContext with DB path, SQL path, JWT secret, JWT algorithm, token TTL.
3. Keep SQL schema in sql/auth/*.sql, never inline large DDL in Python.
4. Build DB helper functions around context.
5. Use Argon2 for password hashing.
6. Put JWT create/decode in a dedicated module.
7. Add dependency for token validation and separate role checker.
8. Keep routes thin; business logic belongs in helpers/services.
9. Add tests for hashing, jwt, database, login, register, protected, rbac.
10. Add auth service to compose and route through nginx.
11. Keep auth DB runtime file out of Git and out of DVC.
12. Move secrets out of plain config for production (env/secret manager).

## 5) Minimal Boilerplate Snippets

### auth.yml fields

```yaml
database: "data/raw/auth.duckdb"
init_sql: "sql/auth/user.sql"
jwt_secret_key: "change-me-in-production"
jwt_algorithm: "HS256"
access_token_expire_minutes: 30
```

### SQL schema starter

```sql
CREATE SEQUENCE IF NOT EXISTS user_id_seq START 1;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY DEFAULT nextval('user_id_seq'),
    username VARCHAR UNIQUE NOT NULL,
    password_hashed VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'user'
);
```

### Route protection pattern

```python
@router.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "Access granted", "user": user}
```

### Role guard pattern

```python
@router.get("/admin-only")
def admin_only(user=Depends(require_role("admin"))):
    return {"ok": True}
```

## 6) Production Hardening Roadmap

Phase 1: Baseline
1. Done: central config and context.
2. Done: SQL-managed schema.
3. Done: nginx and compose integration.

Phase 2: Security hardening
1. Move jwt_secret_key to environment or secret manager.
2. Add token refresh strategy.
3. Add password policy and lockout/rate limit.
4. Add audit logs for login and register actions.

Phase 3: Platform integration
1. Add gateway-level validation for protected upstream routes.
2. Add service-to-service trust model.
3. Add centralized user/role admin endpoints.

Phase 4: Operability
1. Add auth health endpoint and readiness semantics.
2. Add auth metrics (login success/fail, token errors).
3. Add dashboards and alerts for auth failure spikes.

## 7) Fast Troubleshooting Cheatsheet

1. 401 on protected route
- Check token exists and is Bearer format.
- Check jwt secret/algorithm match between issue and decode.
- Check token expiration.

2. User cannot login
- Check user exists in users table.
- Check hash verification.
- Check register flow stored the hash correctly.

3. Nginx route fails
- Check auth service is running in compose.
- Check nginx upstream points to auth:8000.
- Check location block is /auth/ and not rewritten incorrectly.

4. Container restart loop
- Check docker compose logs auth.
- Check config paths exist in container (/app/configs, /app/sql, /app/data).

## 8) Commands You Will Reuse

```bash
# Auth tests
uv run pytest services/auth/tests/

# Start auth and nginx only
docker compose up -d base auth nginx

# Register through nginx
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123","role":"user"}'

# Login through nginx
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
```

---

If you copy this pattern to a new project, keep the same layer boundaries:
config -> context -> storage/security helpers -> dependencies -> routes -> deployment.
That separation is the main reason this auth module stays maintainable.
