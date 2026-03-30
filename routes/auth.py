"""
Auth API Blueprint — Login, Signup, Logout, Auth Check.
"""

import re
import logging
from flask import Blueprint, request, jsonify, session

from models.user import create_user, get_user_by_email, get_user_by_id, verify_password

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _success(data, status=200):
    return jsonify({"success": True, "data": data, "error": None}), status


def _error(code, message, status=400):
    return jsonify({"success": False, "data": None, "error": {"code": code, "message": message}}), status


def _validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Create a new user account."""
    data = request.get_json(silent=True)
    if not data:
        return _error("INVALID_REQUEST", "Request body must be valid JSON.")

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm = data.get("confirm_password", "")

    # Validation
    if not name or len(name) < 2:
        return _error("INVALID_NAME", "Name must be at least 2 characters.")
    if not email or not _validate_email(email):
        return _error("INVALID_EMAIL", "Please enter a valid email address.")
    if not password or len(password) < 6:
        return _error("WEAK_PASSWORD", "Password must be at least 6 characters.")
    if password != confirm:
        return _error("PASSWORD_MISMATCH", "Passwords do not match.")

    user_id = create_user(name, email, password)
    if user_id is None:
        return _error("EMAIL_EXISTS", "An account with this email already exists.")

    # Auto-login after signup
    session["user_id"] = user_id
    session["user_name"] = name
    session["user_email"] = email

    logger.info("User signed up: %s", email)
    return _success({"user_id": user_id, "name": name, "email": email}, 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate and log in a user."""
    data = request.get_json(silent=True)
    if not data:
        return _error("INVALID_REQUEST", "Request body must be valid JSON.")

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return _error("MISSING_CREDENTIALS", "Email and password are required.")

    user = get_user_by_email(email)
    if user is None or not verify_password(user["password_hash"], password):
        return _error("INVALID_CREDENTIALS", "Invalid email or password.", 401)

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    logger.info("User logged in: %s", email)
    return _success({
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"],
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Log out the current user."""
    session.clear()
    return _success({"message": "Logged out successfully."})


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """Get the current logged-in user's info."""
    user_id = session.get("user_id")
    if not user_id:
        return _error("NOT_AUTHENTICATED", "You are not logged in.", 401)

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return _error("USER_NOT_FOUND", "User account not found.", 401)

    return _success({
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"],
    })
