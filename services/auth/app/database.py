# services/auth/app/database.py
"""Initializes the database connection and exposes helper functions to query users."""

from pathlib import Path

import duckdb

from .hashing import hash_password
from .models import User

DB_PATH = Path("auth.duckhub")


def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH))


def init_db():
    conn: duckdb.DuckDBPyConnection = get_connection()
    # Create a sequence to handle auto-incrementing
    conn.execute("CREATE SEQUENCE IF NOT EXISTS user_id_seq START 1")
    # Create the table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER DEFAULT KEY DEFAULT nextval('user_id_seq'),
            username VARCHAR NOT NULL,
            password_hashed VARCHAR NOT NULL,
            role VARCHAR DEFAULT 'user'
        );
    """)
    conn.close()


def create_user(username: str, password_hashed: str, role: str = "user") -> User | None:
    if user_exists(username):
        print(f"User '{username}' already exists.")
        return None

    conn: duckdb.DuckDBPyConnection = get_connection()
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


def get_user(username: str) -> User | None:
    conn: duckdb.DuckDBPyConnection = get_connection()
    row = conn.execute(
        "SELECT id, username, password_hashed, role FROM users WHERE username = ?", [username]
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return User(id=row[0], username=row[1], password_hashed=row[2], role=row[3])


def user_exists(username: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1;", [username]).fetchone()
    conn.close()
    return row is not None


def _print_users_table():
    conn = get_connection()
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
    init_db()
    create_user("alice", hash_password("mypassword"), "admin")
    create_user("bob", hash_password("secret"), "user")

    _print_users_table()
