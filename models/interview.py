"""
Interview model — persist and query interview sessions in SQLite.
"""

import json
import logging
from datetime import datetime
from database import get_db, close_db

logger = logging.getLogger(__name__)


def save_interview(session_data):
    """Save or update an interview session to the database."""
    conn = get_db()
    try:
        avg_score = 0
        evaluations = session_data.get("evaluations", [])
        if evaluations:
            scores = [e.get("score", 0) for e in evaluations]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        completed_at = None
        if session_data.get("status") == "completed":
            completed_at = datetime.utcnow().isoformat()

        conn.execute("""
            INSERT OR REPLACE INTO interviews 
            (id, user_id, role, experience_level, cv_filename, cv_text, jd_text,
             questions, answers, evaluations, status, average_score, 
             total_questions, answered_questions, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data["id"],
            session_data.get("user_id", 0),
            session_data["role"],
            session_data["experience_level"],
            session_data.get("cv_filename"),
            session_data.get("cv_text"),
            session_data.get("jd_text"),
            json.dumps(session_data.get("questions", [])),
            json.dumps(session_data.get("answers", [])),
            json.dumps(evaluations),
            session_data.get("status", "in_progress"),
            avg_score,
            len(session_data.get("questions", [])),
            len(session_data.get("answers", [])),
            session_data.get("created_at", datetime.utcnow().isoformat()),
            completed_at,
        ))
        conn.commit()
        logger.info("Saved interview %s to database", session_data["id"])
    finally:
        close_db(conn)


def get_user_interviews(user_id, limit=50):
    """Get a list of interviews for a user, most recent first."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, role, experience_level, status, average_score, 
                   total_questions, answered_questions, created_at, completed_at,
                   cv_filename
            FROM interviews 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(row) for row in rows]
    finally:
        close_db(conn)


def get_interview(interview_id):
    """Get full interview data by ID."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM interviews WHERE id = ?",
            (interview_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        # Parse JSON fields
        data["questions"] = json.loads(data["questions"] or "[]")
        data["answers"] = json.loads(data["answers"] or "[]")
        data["evaluations"] = json.loads(data["evaluations"] or "[]")
        return data
    finally:
        close_db(conn)
