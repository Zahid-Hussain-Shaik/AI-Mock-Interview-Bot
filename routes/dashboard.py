"""
Dashboard API Blueprint — Interview history for logged-in users.
"""

import logging
from flask import Blueprint, request, jsonify, session

from models.interview import get_user_interviews, get_interview

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _success(data, status=200):
    return jsonify({"success": True, "data": data, "error": None}), status


def _error(code, message, status=400):
    return jsonify({"success": False, "data": None, "error": {"code": code, "message": message}}), status


@dashboard_bp.route("/interviews", methods=["GET"])
def list_interviews():
    """Get all interviews for the logged-in user."""
    user_id = session.get("user_id")
    if not user_id:
        return _error("NOT_AUTHENTICATED", "You are not logged in.", 401)

    interviews = get_user_interviews(user_id)
    return _success({"interviews": interviews})


@dashboard_bp.route("/interviews/<interview_id>", methods=["GET"])
def get_interview_detail(interview_id):
    """Get full details of a specific interview."""
    user_id = session.get("user_id")
    if not user_id:
        return _error("NOT_AUTHENTICATED", "You are not logged in.", 401)

    interview = get_interview(interview_id)
    if not interview or interview["user_id"] != user_id:
        return _error("NOT_FOUND", "Interview not found.", 404)

    return _success(interview)
