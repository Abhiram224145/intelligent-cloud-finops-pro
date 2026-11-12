import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path

import streamlit as st

# SQLite database used by the current prototype.
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "project databases"
DB_PATH = DB_DIR / "users.db"
PBKDF2_ITERATIONS = 300_000
VALID_ROLES = ("Resource Owner", "Manager", "Admin")


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                role TEXT NOT NULL DEFAULT 'Resource Owner'
            )"""
        )
        # Upgrade databases created by the older version of this app.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "role" not in columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'Resource Owner'"
            )


def hash_password(password, salt_hex=None):
    if salt_hex is None:
        salt_hex = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS
    ).hex()
    return salt_hex, password_hash


def register_user(username, password):
    username = username.strip()
    if not 3 <= len(username) <= 50:
        return False, "Username must be between 3 and 50 characters."
    if any(ch.isspace() for ch in username):
        return False, "Username cannot contain spaces."
    if len(password) < 12:
        return False, "Password must contain at least 12 characters."

    salt, password_hash = hash_password(password)
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, salt, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, salt, password_hash, "Resource Owner"),
            )
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "That username already exists."


def verify_user(username, password):
    username = username.strip()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT username, salt, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        hash_password(password, "0" * 32)
        return False, None, None
    saved_username, salt, saved_hash, role = row
    _, entered_hash = hash_password(password, salt)
    return hmac.compare_digest(saved_hash, entered_hash), saved_username, role


def get_all_users():
    """Return user records in the column format expected by the admin dashboard."""
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT username, role, created_at FROM users ORDER BY username COLLATE NOCASE"
        ).fetchall()
    return [
        {"Username": username, "Role": role, "Created At": created_at}
        for username, role, created_at in rows
    ]


def update_user_role(username, new_role):
    if new_role not in VALID_ROLES:
        return False, "Invalid role selected."
    initialize_database()
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET role = ? WHERE username = ?", (new_role, username)
        )
        if cursor.rowcount == 0:
            return False, "User not found."
    return True, f"Role for {username} updated to {new_role}."


def _set_authenticated_user(username, role):
    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    st.session_state["role"] = role or "Resource Owner"


def show_login():
    initialize_database()

    if st.session_state.get("logged_in") is True:
        st.sidebar.success(f"Signed in as {st.session_state.get('username', 'User')}")
        if st.sidebar.button("Log out", key="auth_logout"):
            for key in ("logged_in", "username", "role"):
                st.session_state.pop(key, None)
            st.rerun()
        return True
