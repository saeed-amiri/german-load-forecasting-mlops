# services/auth/app/database.py
"""Initializes the auth database and provides user query helpers."""

import duckdb

from services.auth.context import AuthContext, get_auth_context

from .models import User


def get_connection(ctx: AuthContext | None = None) -> duckdb.DuckDBPyConnection:
    active_ctx = ctx or get_auth_context()
    return duckdb.connect(str(active_ctx.database_path))


def init_db(ctx: AuthContext | None = None) -> None:
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
    active_ctx = ctx or get_auth_context()
    conn = get_connection(active_ctx)
    row = conn.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1;", [username]).fetchone()
    conn.close()
    return row is not None


def _print_users_table(ctx: AuthContext | None = None) -> None:
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
