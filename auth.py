
import streamlit as st
import sqlite3
import hashlib
import secrets
import os

DB_FOLDER = "project databases"
DB_PATH = os.path.join(DB_FOLDER, "users.db")


def get_connection():
    os.makedirs(DB_FOLDER, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        300000,
    ).hex()

    return salt, password_hash


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)")
        }

        if "role" not in columns:
            conn.execute(
                "ALTER TABLE users "
                "ADD COLUMN role TEXT NOT NULL DEFAULT 'Resource Owner'"
            )


def register_user(username, password, role="Resource Owner"):
    username = username.strip()

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if len(username) > 50:
        return False, "Username must not exceed 50 characters."

    if len(password) < 12:
        return False, "Use a password with at least 12 characters."

    if role not in ("Admin", "Resource Owner", "Manager"):
        return False, "Invalid role."

    salt, password_hash = hash_password(password)

    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO users
                   (username, salt, password_hash, role)
                   VALUES (?, ?, ?, ?)""",
                (username, salt, password_hash, role),
            )

        return True, "Account created. You can now log in."

    except sqlite3.IntegrityError:
        return False, "That username already exists."
    
def verify_user(username, password):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT username, salt, password_hash, role
               FROM users
               WHERE username = ?""",
            (username.strip(),),
        ).fetchone()

    if row is None:
        return None

    saved_username, salt, saved_hash, role = row

    _, entered_hash = hash_password(password, salt)

    if not secrets.compare_digest(saved_hash, entered_hash):
        return None

    return {
        "username": saved_username,
        "role": role,
    }

def show_login():
    initialize_database()

    if st.session_state.get("logged_in", False):
        st.sidebar.success(
            f"Logged in as {st.session_state['username']}"
        )
        st.sidebar.info(
    f"Role: {st.session_state.get('role', 'Resource Owner')}"
)

        if st.sidebar.button("Log out"):
            st.session_state.pop("logged_in", None)
            st.session_state.pop("username", None)
            st.session_state.pop("role", None)
            st.rerun()

        return True

    st.title("Cloud FinOps Optimizer")
    st.subheader("Login or create your account")

    choice = st.radio(
        "Choose an option",
        ["Login", "Create Account"],
        horizontal=True,
    )

    if choice == "Create Account":
        with st.form("signup_form"):
            username = st.text_input("Choose a username")
            password = st.text_input(
                "Create a password",
                type="password",
            )
            confirm = st.text_input(
                "Confirm password",
                type="password",
            )
            submitted = st.form_submit_button("Create Account")

        if submitted:
            if password != confirm:
                st.error("The passwords do not match.")
            else:
                success, message = register_user(username, password)
                if success:
                    st.success(message)
                    st.info("Select Login above to sign in.")
                else:
                    st.error(message)

    else:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input(
                "Password",
                type="password",
            )
            submitted = st.form_submit_button("Login")

        if submitted:
            user = verify_user(username, password)

            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = user["username"]
                st.session_state["role"] = user["role"]
                st.rerun()
            else:
                st.error("Invalid username or password.")

def get_all_users():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT username, role FROM users ORDER BY username"
        ).fetchall()

    return [
        {"Username": row[0], "Role": row[1]}
        for row in rows
    ]
def update_user_role(username, new_role):
    allowed_roles = ("Admin", "Manager", "Resource Owner")

    if new_role not in allowed_roles:
        return False, "Invalid role."

    with get_connection() as conn:
        current = conn.execute(
            "SELECT role FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

        if current is None:
            return False, "User not found."

        if current[0] == "Admin" and new_role != "Admin":
            admin_count = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'Admin'"
            ).fetchone()[0]

            if admin_count <= 1:
                return False, "Cannot remove the last Admin."

        conn.execute(
            "UPDATE users SET role = ? WHERE username = ?",
            (new_role, username.strip()),
        )

    return True, "Role updated successfully."
    allowed_roles = ("Admin", "Manager", "Resource Owner")

    if new_role not in allowed_roles:
        return False

    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET role = ? WHERE username = ?",
            (new_role, username.strip()),
        )
def fix_abhiram_role():
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET role = ? WHERE username = ?",
            ("Admin", "Abhiram"),
        )
        row = conn.execute(
            "SELECT username, role FROM users WHERE username = ?",
            ("Abhiram",),
        ).fetchone()
    print(row)
    