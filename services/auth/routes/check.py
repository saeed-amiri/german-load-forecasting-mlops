"""
nginx auth_request subrequest handler.

nginx sends a subrequest to /auth/check before proxying any protected location.
This route validates the JWT and checks the role against ROLE_MATRIX.
Returns 200 (allow) or 403 (deny) — nginx uses the status code only.
"""

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response

from ..app.jwt_utils import decode_access_token
from ..app.rbac import ADMIN_ROLE, ROLE_MATRIX

router = APIRouter()


@router.get("/check")
def auth_check(
    request: Request,
    authorization: str | None = Header(default=None),
    x_original_uri: str | None = Header(default=None),
) -> Response:
    """
    Called by nginx auth_request for every protected location.

    nginx passes:
      - Authorization: Bearer <token>   (forwarded from the original request)
      - X-Original-URI: /airflow/...    (the path being accessed)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.removeprefix("Bearer ")
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_role = payload.get("role")

    # Determine which matrix key matches the requested path
    path = x_original_uri or ""
    allowed_roles = _lookup_matrix(path)

    if user_role == ADMIN_ROLE or user_role in allowed_roles:
        return Response(status_code=200)

    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _lookup_matrix(path: str) -> set[str]:
    """Return the allowed roles for the longest matching prefix in ROLE_MATRIX."""
    for prefix in sorted(ROLE_MATRIX, key=len, reverse=True):
        if path.startswith(prefix):
            return ROLE_MATRIX[prefix]
    return set()
