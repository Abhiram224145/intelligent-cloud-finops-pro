import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path

import streamlit as st


# DATABASE CONFIGURATION
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "project databases"
DB_PATH = DB_DIR / "users.db"

PBKDF2_ITERATIONS = 300000

ALLOWED_ROLES = (
    "Admin",
    "Manager",
    "Resource Owner"
)


# DATABASE CONNECTION
def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


# INITIALIZE DATABASE
def initialize_database():
    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Resource Owner'
            )
        """)

        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(users)"
            )
        }

        if "role" not in columns:
            conn.execute("""
                ALTER TABLE users
                ADD COLUMN role TEXT NOT NULL
                DEFAULT 'Resource Owner'
            """)


# PASSWORD HASHING
def hash_password(password, salt_hex=None):

    if salt_hex is None:
        salt_hex = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PBKDF2_ITERATIONS
    ).hex()

    return salt_hex, password_hash


# REGISTER USER
def register_user(username, password):

    username = username.strip()

    if not 3 <= len(username) <= 50:
        return False, "Username must contain 3 to 50 characters."

    if any(char.isspace() for char in username):
        return False, "Username cannot contain spaces."

    if len(password) < 12:
        return False, "Password must contain at least 12 characters."

    salt, password_hash = hash_password(password)

    try:
        with get_connection() as conn:

            conn.execute("""
                INSERT INTO users
                (username, salt, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                salt,
                password_hash,
                "Resource Owner"
            ))

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "Username already exists."


# VERIFY USER
def verify_user(username, password):

    username = username.strip()

    with get_connection() as conn:

        row = conn.execute("""
            SELECT username, salt, password_hash, role
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

    if row is None:
        return None

    saved_username, salt, saved_hash, role = row

    _, entered_hash = hash_password(password, salt)

    if not hmac.compare_digest(saved_hash, entered_hash):
        return None

    return {
        "username": saved_username,
        "role": role
    }


# SESSION LOGIN
def set_logged_in_user(user):

    st.session_state["logged_in"] = True
    st.session_state["username"] = user["username"]
    st.session_state["role"] = user["role"]


# LOGOUT
def logout():

    for key in (
        "logged_in",
        "username",
        "role"
    ):
        st.session_state.pop(key, None)

    st.rerun()


# LOGIN AND REGISTRATION PAGE
def show_login():

    initialize_database()

    # ALREADY LOGGED IN
    if st.session_state.get("logged_in") is True:

        st.sidebar.success(
            f"Logged in as {st.session_state.get('username', 'User')}"
        )

        st.sidebar.info(
            f"Role: {st.session_state.get('role', 'Resource Owner')}"
        )

        if st.sidebar.button(
            "Log out",
            key="auth_logout"
        ):
            logout()

        return True

    st.title("☁️ Cloud FinOps Optimizer")

    st.subheader("Login or create your account")

    choice = st.radio(
        "Choose an option",
        ["Login", "Create Account"],
        horizontal=True,
        key="auth_choice"
    )

    # CREATE ACCOUNT
    if choice == "Create Account":

        with st.form("signup_form"):

            new_username = st.text_input(
                "Choose a username"
            )

            new_password = st.text_input(
                "Create a password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            signup_submitted = st.form_submit_button(
                "Create Account",
                type="primary",
                use_container_width=True
            )

        if signup_submitted:

            if new_password != confirm_password:

                st.error("Passwords do not match.")

            else:

                success, message = register_user(
                    new_username,
                    new_password
                )

                if success:

                    # AUTOMATIC LOGIN AFTER REGISTRATION
                    user = {
                        "username": new_username.strip(),
                        "role": "Resource Owner"
                    }

                    set_logged_in_user(user)

                    st.success(message)

                    st.rerun()

                else:

                    st.error(message)

    # EXISTING USER LOGIN
    else:

        with st.form("login_form"):

            username = st.text_input(
                "Username"
            )

            password = st.text_input(
                "Password",
                type="password"
            )

            login_submitted = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True
            )

        if login_submitted:

            user = verify_user(
                username,
                password
            )

            if user:

                set_logged_in_user(user)

                st.rerun()

            else:

                st.error("Invalid username or password.")

    return False


# GET ALL USERS
def get_all_users():

    initialize_database()

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT username, role
            FROM users
            ORDER BY username
        """).fetchall()

    return [
        {
            "Username": row[0],
            "Role": row[1]
        }
        for row in rows
    ]


# UPDATE USER ROLE
def update_user_role(username, new_role):

    if new_role not in ALLOWED_ROLES:

        return False, "Invalid role."

    initialize_database()

    with get_connection() as conn:

        current = conn.execute("""
            SELECT role
            FROM users
            WHERE username = ?
        """, (username.strip(),)).fetchone()

        if current is None:

            return False, "User not found."

        # PROTECT THE LAST ADMIN
        if current[0] == "Admin" and new_role != "Admin":

            admin_count = conn.execute("""
                SELECT COUNT(*)
                FROM users
                WHERE role = 'Admin'
            """).fetchone()[0]

            if admin_count <= 1:

                return False, "Cannot remove the last Admin."

        conn.execute("""
            UPDATE users
            SET role = ?
            WHERE username = ?
        """, (
            new_role,
            username.strip()
        ))

    return True, "Role updated successfully."


# SET ABHIRAM AS ADMIN
def fix_abhiram_role():

    initialize_database()

    with get_connection() as conn:

        conn.execute("""
            UPDATE users
            SET role = ?
            WHERE username = ?
        """, (
            "Admin",
            "Abhiram"
        ))

        return conn.execute("""
            SELECT username, role
            FROM users
            WHERE username = ?
        """, ("Abhiram",)).fetchone()
