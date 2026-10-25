import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path

import streamlit as st

# Local development database. Use persistent managed storage before public deployment.
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "project databases"
DB_PATH = DB_DIR / "users.db"
PBKDF2_ITERATIONS = 300_000


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


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
                "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                (username, salt, password_hash),
            )
        return True, "Account created. You can now log in."
    except sqlite3.IntegrityError:
        return False, "That username already exists."


def verify_user(username, password):
    username = username.strip()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT username, salt, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        # Reduce obvious timing differences for unknown usernames.
        hash_password(password, "0" * 32)
        return False, None
    saved_username, salt, saved_hash = row
    _, entered_hash = hash_password(password, salt)
    return hmac.compare_digest(saved_hash, entered_hash), saved_username


def show_login():
    initialize_database()

    if st.session_state.get("logged_in") is True:
        st.sidebar.success(f"Signed in as {st.session_state.get('username', 'User')}")
        if st.sidebar.button("Log out", key="auth_logout"):
            st.session_state.pop("logged_in", None)
            st.session_state.pop("username", None)
            st.rerun()
        return True

    st.title("☁️ Cloud FinOps Optimizer")
    st.subheader("Sign in or create an account")
    login_tab, signup_tab = st.tabs(["Login", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            valid, saved_username = verify_user(username, password)
            if valid:
                st.session_state["logged_in"] = True
                st.session_state["username"] = saved_username
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with signup_tab:
        st.caption("Choose a username and a password of at least 12 characters.")
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username", key="signup_username")
            new_password = st.text_input("Create password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm")
            signup_submitted = st.form_submit_button("Create Account", use_container_width=True)
        if signup_submitted:
            if new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                success, message = register_user(new_username, new_password)
                if success:
                    # Sign the new user in immediately and let the main app continue
                    # to the dashboard on the next Streamlit rerun.
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = new_username.strip()
                    st.rerun()
                else:
                    st.error(message)

    return False
