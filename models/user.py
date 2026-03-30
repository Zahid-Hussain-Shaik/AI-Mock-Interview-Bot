"""
User model — create, authenticate, and query users.
"""

import logging
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, close_db

logger = logging.getLogger(__name__)


def create_user(name, email, password):
    """
    Create a new user account.
    Returns the user id on success, or None if email already exists.
    """
    conn = get_db()
    try:
        password_hash = generate_password_hash(password)
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), password_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid
        logger.info("Created user %s (id=%d)", email, user_id)
        return user_id
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            logger.warning("Email already exists: %s", email)
            return None
        logger.error("Error creating user: %s", str(e))
        raise
    finally:
        close_db(conn)


def get_user_by_email(email):
    """Get a user by email. Returns dict or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        close_db(conn)


def get_user_by_id(user_id):
    """Get a user by ID. Returns dict or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        close_db(conn)


def verify_password(stored_hash, password):
    """Check a password against the stored hash."""
    return check_password_hash(stored_hash, password)
