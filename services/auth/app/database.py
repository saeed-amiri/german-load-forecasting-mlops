# services/auth/app/database.py
"""
DuckDB-backed persistence layer for the auth service.

Responsibilities:
- Opening and closing DuckDB connections against the configured database file.
- Bootstrapping the schema from the SQL init script on startup.
- CRUD helpers for the ``users`` table (create, read, existence check).

All public functions accept an optional ``ctx: AuthContext`` parameter so they
can be called with an injected context in tests without touching global state.
When ``ctx`` is omitted, the module falls back to the process-wide singleton
returned by :func:`~services.auth.context.get_auth_context`.
"""

import duckdb

from services.auth.context import AuthContext, get_auth_context

from .models import User


def get_connection(ctx: AuthContext | None = None) -> duckdb.DuckDBPyConnection:
    """Open and return a new DuckDB connection to the auth database.

    Each call creates a fresh connection; callers are responsible for closing
    it after use.

    Args:
        ctx: Optional auth context supplying the database path. Defaults to
            the process-wide singleton.

    Returns:
        An open :class:`duckdb.DuckDBPyConnection` pointed at the auth DB file.
    """
    active_ctx = ctx or get_auth_context()
    return duckdb.connect(str(active_ctx.database_path))


def init_db(ctx: AuthContext | None = None) -> None:
    """Bootstrap the auth database schema.

    Reads the SQL init script referenced by the context and executes it against
    the database. Safe to call on every startup — the script should use
    ``CREATE TABLE IF NOT EXISTS`` semantics to avoid wiping existing data.

    Args:
        ctx: Optional auth context supplying both the database path and the
            path to the SQL init script. Defaults to the process-wide singleton.
    """
    active_ctx = ctx or get_auth_context()
    sql = active_ctx.init_sql_path.read_text(encoding="utf-8")

    conn = get_connection(active_ctx)
    conn.execute(sql)
    conn.close()


def create_user(
    username: str,
    password_hashed: str,
    role: str = "user",
    ctx: AuthContext | None = None,
) -> User | None:
    """Insert a new user record and return the created ``User``.

    Does nothing and returns ``None`` if a user with the same username already
    exists, leaving duplicate-handling to the caller.

    Args:
        username: Unique display name for the user.
        password_hashed: Pre-hashed password string (bcrypt hash). Plain-text
            passwords must be hashed before being passed here.
        role: RBAC role assigned to the user. Defaults to ``"user"``.
        ctx: Optional auth context. Defaults to the process-wide singleton.

    Returns:
        The newly created :class:`~services.auth.app.models.User` with its
        assigned database ``id``, or ``None`` if the username is already taken.
    """
    active_ctx = ctx or get_auth_context()

    if user_exists(username, active_ctx):
        return None

    conn = get_connection(active_ctx)
    result = conn.execute(
        """
        INSERT INTO users (username, password_hashed, role)
        VALUES (?, ?, ?)
        RETURNING id, username, password_hashed, role;
        """,
        [username, password_hashed, role],
    ).fetchone()
    conn.close()

    if result is None:
        return None

    return User(id=result[0], username=result[1], password_hashed=result[2], role=result[3])


def get_user(username: str, ctx: AuthContext | None = None) -> User | None:
    """Fetch a single user by username.

    Args:
        username: The username to look up.
        ctx: Optional auth context. Defaults to the process-wide singleton.

    Returns:
        The matching :class:`~services.auth.app.models.User`, or ``None`` if no
        user with that username exists.
    """
    active_ctx = ctx or get_auth_context()
    conn = get_connection(active_ctx)
    row = conn.execute(
        "SELECT id, username, password_hashed, role FROM users WHERE username = ?", [username]
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return User(id=row[0], username=row[1], password_hashed=row[2], role=row[3])


def user_exists(username: str, ctx: AuthContext | None = None) -> bool:
    """Check whether a username is already registered.

    Uses a ``LIMIT 1`` query for efficiency — does not fetch the full row.

    Args:
        username: The username to check.
        ctx: Optional auth context. Defaults to the process-wide singleton.

    Returns:
        ``True`` if the username exists in the database, ``False`` otherwise.
    """
    active_ctx = ctx or get_auth_context()
    conn = get_connection(active_ctx)
    row = conn.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1;", [username]).fetchone()
    conn.close()
    return row is not None


def _print_users_table(ctx: AuthContext | None = None) -> None:
    """Print all rows in the ``users`` table to stdout (debug/dev helper only).

    Not intended for production use. Outputs each user's id, username,
    hashed password, and role.

    Args:
        ctx: Optional auth context. Defaults to the process-wide singleton.
    """
    active_ctx = ctx or get_auth_context()
    conn = get_connection(active_ctx)
    rows = conn.execute("SELECT id, username, password_hashed, role FROM users").fetchall()
    conn.close()

    if not rows:
        print("No users found.")
        return

    print("\n=== USERS TABLE ===")
    for row in rows:
        print(f"id={row[0]}, username={row[1]}, password_hashed={row[2]}, role={row[3]}")
    print("===================\n")


if __name__ == "__main__":
    from .hashing import hash_password

    auth_ctx = get_auth_context()
    init_db(auth_ctx)
    create_user("alice", hash_password("mypassword"), "admin", auth_ctx)
    create_user("bob", hash_password("secret"), "user", auth_ctx)
    _print_users_table(auth_ctx)
