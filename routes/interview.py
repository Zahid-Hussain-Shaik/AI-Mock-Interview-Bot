"""
Interview API Blueprint.
All endpoints return consistent JSON responses.
Requires authentication for all operations.
"""

import logging
from flask import Blueprint, request, jsonify, current_app, session as flask_session

from services.question_generator import generate_questions
from services.answer_evaluator import evaluate_answer
from services.cv_parser import extract_text
from models.interview import save_interview

logger = logging.getLogger(__name__)

interview_bp = Blueprint("interview", __name__, url_prefix="/api/interview")


def _success(data, status=200):
    """Return a standard success response."""
    return jsonify({"success": True, "data": data, "error": None}), status


def _error(code, message, status=400):
    """Return a standard error response."""
    return jsonify({
        "success": False,
        "data": None,
        "error": {"code": code, "message": message},
    }), status


def _require_auth():
    """Check if user is authenticated. Returns user_id or None."""
    return flask_session.get("user_id")


@interview_bp.route("/start", methods=["POST"])
def start_interview():
    """
    Start a new interview session.
    Accepts multipart form data with optional CV file and JD text.
    """
    user_id = _require_auth()
    if not user_id:
        return _error("NOT_AUTHENTICATED", "Please log in to start an interview.", 401)

    # Handle both JSON and multipart form data
    if request.content_type and "multipart/form-data" in request.content_type:
        role = request.form.get("role", "").strip()
        experience_level = request.form.get("experience_level", "").strip()
        jd_text = request.form.get("jd_text", "").strip() or None
        cv_file = request.files.get("cv_file")
    else:
        data = request.get_json(silent=True) or {}
        role = data.get("role", "").strip()
        experience_level = data.get("experience_level", "").strip()
        jd_text = data.get("jd_text", "").strip() or None
        cv_file = None

    if not role:
        return _error("MISSING_ROLE", "Please select a job role.")
    if not experience_level:
        return _error("MISSING_LEVEL", "Please select an experience level.")

    valid_roles = [
        "Software Engineer", "Frontend Developer", "Backend Developer",
        "Full Stack Developer", "Data Scientist", "DevOps Engineer",
        "Product Manager", "ML Engineer", "Data Analyst", "Cloud Architect",
    ]
    valid_levels = ["Entry Level", "Mid Level", "Senior", "Lead/Principal"]

    if role not in valid_roles:
        return _error("INVALID_ROLE", f"Invalid role. Choose from: {', '.join(valid_roles)}")
    if experience_level not in valid_levels:
        return _error("INVALID_LEVEL", f"Invalid level. Choose from: {', '.join(valid_levels)}")

    # Parse CV if uploaded
    cv_text = None
    cv_filename = None
    if cv_file and cv_file.filename:
        cv_filename = cv_file.filename
        allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"pdf", "docx", "txt"})
        ext = cv_filename.rsplit(".", 1)[-1].lower() if "." in cv_filename else ""
        if ext not in allowed:
            return _error("INVALID_FILE", f"Unsupported file format. Allowed: {', '.join(allowed)}")
        try:
            cv_text = extract_text(cv_file, cv_filename)
            logger.info("Extracted %d chars from CV: %s", len(cv_text), cv_filename)
        except Exception as e:
            logger.warning("CV parsing failed: %s", str(e))
            return _error("CV_PARSE_ERROR", f"Could not parse CV: {str(e)}")

    session_mgr = current_app.config["SESSION_MANAGER"]
    claude = current_app.config["CLAUDE_CLIENT"]
    min_q = current_app.config.get("MIN_QUESTIONS", 8)
    max_q = current_app.config.get("MAX_QUESTIONS", 12)

    # Create session
    session_id = session_mgr.create_session(
        role, experience_level,
        user_id=user_id,
        cv_text=cv_text,
        cv_filename=cv_filename,
        jd_text=jd_text,
    )
    logger.info("Created session %s for user %d: %s %s", session_id, user_id, experience_level, role)

    try:
        # Generate questions (with optional CV/JD context)
        questions = generate_questions(
            claude, role, experience_level, min_q, max_q,
            cv_text=cv_text, jd_text=jd_text,
        )
        session_mgr.set_questions(session_id, questions)
    except Exception as e:
        logger.error("Failed to generate questions: %s", str(e))
        return _error(
            "GENERATION_FAILED",
            "Failed to generate interview questions. Please try again.",
            500,
        )

    # Save initial session to DB
    session_data = session_mgr.get_session(session_id)
    try:
        save_interview(session_data)
    except Exception as e:
        logger.warning("Failed to save interview to DB: %s", str(e))

    return _success({
        "session_id": session_id,
        "total_questions": len(questions),
        "role": role,
        "experience_level": experience_level,
        "current_question": questions[0],
        "has_cv": cv_text is not None,
        "has_jd": jd_text is not None,
    })


@interview_bp.route("/<session_id>/question", methods=["GET"])
def get_current_question(session_id):
    """Get the current question for a session."""
    user_id = _require_auth()
    if not user_id:
        return _error("NOT_AUTHENTICATED", "Please log in.", 401)

    session_mgr = current_app.config["SESSION_MANAGER"]
    session = session_mgr.get_session(session_id)

    if session is None:
        return _error("SESSION_NOT_FOUND", "Session not found or expired.", 404)

    if session["status"] == "completed":
        return _success({
            "completed": True,
            "message": "All questions have been answered.",
            "current": session["current_index"],
            "total": len(session["questions"]),
        })

    idx = session["current_index"]
    if idx >= len(session["questions"]):
        return _error("NO_MORE_QUESTIONS", "All questions have been answered.")

    return _success({
        "completed": False,
        "current_question": session["questions"][idx],
        "current": idx + 1,
        "total": len(session["questions"]),
        "role": session["role"],
        "experience_level": session["experience_level"],
    })


@interview_bp.route("/<session_id>/answer", methods=["POST"])
def submit_answer(session_id):
    """
    Submit an answer for the current question.
    Body: { "answer": "..." }
    Returns: evaluation + next question (if any).
    """
    user_id = _require_auth()
    if not user_id:
        return _error("NOT_AUTHENTICATED", "Please log in.", 401)

    session_mgr = current_app.config["SESSION_MANAGER"]
    claude = current_app.config["CLAUDE_CLIENT"]

    session = session_mgr.get_session(session_id)
    if session is None:
        return _error("SESSION_NOT_FOUND", "Session not found or expired.", 404)

    if session["status"] == "completed":
        return _error("SESSION_COMPLETED", "This interview session is already completed.")

    data = request.get_json(silent=True)
    if not data:
        return _error("INVALID_REQUEST", "Request body must be valid JSON.")

    answer = data.get("answer", "").strip()

    idx = session["current_index"]
    question = session["questions"][idx]

    try:
        evaluation = evaluate_answer(
            claude, question, answer,
            session["role"], session["experience_level"],
        )
    except Exception as e:
        logger.error("Failed to evaluate answer: %s", str(e))
        return _error(
            "EVALUATION_FAILED",
            "Failed to evaluate your answer. Please try again.",
            500,
        )

    # Record the answer and evaluation
    session_mgr.submit_answer(session_id, answer, evaluation)

    # Refresh session state
    updated_session = session_mgr.get_session(session_id)
    is_completed = updated_session["status"] == "completed"

    # Save to DB after each answer
    try:
        save_interview(updated_session)
    except Exception as e:
        logger.warning("Failed to save to DB: %s", str(e))

    response_data = {
        "evaluation": evaluation,
        "question_number": idx + 1,
        "total_questions": len(session["questions"]),
        "completed": is_completed,
    }

    if not is_completed:
        next_idx = updated_session["current_index"]
        response_data["next_question"] = updated_session["questions"][next_idx]

    return _success(response_data)


@interview_bp.route("/<session_id>/results", methods=["GET"])
def get_results(session_id):
    """Get the complete results for a finished interview session."""
    session_mgr = current_app.config["SESSION_MANAGER"]
    session = session_mgr.get_session(session_id)

    if session is None:
        # Try loading from database
        from models.interview import get_interview
        session = get_interview(session_id)
        if session is None:
            return _error("SESSION_NOT_FOUND", "Session not found or expired.", 404)

    questions = session["questions"]
    answers = session["answers"]
    evaluations = session["evaluations"]

    # Build per-question results
    question_results = []
    for i in range(len(answers)):
        question_results.append({
            "question": questions[i],
            "answer": answers[i],
            "evaluation": evaluations[i],
        })

    # Calculate aggregate stats
    scores = [e["score"] for e in evaluations]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    # Category breakdown
    category_scores = {}
    for i, e in enumerate(evaluations):
        cat = questions[i].get("category", "general")
        if cat not in category_scores:
            category_scores[cat] = []
        category_scores[cat].append(e["score"])

    category_averages = {
        cat: round(sum(s) / len(s), 1)
        for cat, s in category_scores.items()
    }

    # Aggregate strengths and weaknesses
    all_strengths = []
    all_weaknesses = []
    for e in evaluations:
        all_strengths.extend(e.get("strengths", []))
        all_weaknesses.extend(e.get("weaknesses", []))

    # Score distribution
    score_distribution = {
        "excellent (9-10)": sum(1 for s in scores if s >= 9),
        "strong (7-8)": sum(1 for s in scores if 7 <= s <= 8),
        "adequate (5-6)": sum(1 for s in scores if 5 <= s <= 6),
        "needs improvement (1-4)": sum(1 for s in scores if s <= 4),
    }

    # Performance level
    if avg_score >= 8.5:
        performance = "Outstanding"
    elif avg_score >= 7:
        performance = "Strong"
    elif avg_score >= 5.5:
        performance = "Adequate"
    elif avg_score >= 4:
        performance = "Needs Improvement"
    else:
        performance = "Significant Gaps"

    return _success({
        "session_id": session.get("id", session_id),
        "role": session["role"],
        "experience_level": session["experience_level"],
        "status": session.get("status", "completed"),
        "total_questions": len(questions),
        "answered_questions": len(answers),
        "has_cv": bool(session.get("cv_text")),
        "has_jd": bool(session.get("jd_text")),
        "results": question_results,
        "aggregate": {
            "average_score": avg_score,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "performance_level": performance,
            "category_averages": category_averages,
            "score_distribution": score_distribution,
            "key_strengths": all_strengths[:8],
            "key_weaknesses": all_weaknesses[:8],
        },
    })


@interview_bp.route("/<session_id>/progress", methods=["GET"])
def get_progress(session_id):
    """Get session progress information."""
    session_mgr = current_app.config["SESSION_MANAGER"]
    progress = session_mgr.get_progress(session_id)

    if progress is None:
        return _error("SESSION_NOT_FOUND", "Session not found or expired.", 404)

    return _success(progress)
