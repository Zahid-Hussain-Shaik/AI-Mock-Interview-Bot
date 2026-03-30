"""
Thread-safe server-side session manager for interview sessions.
"""

import uuid
import threading
from datetime import datetime, timedelta


class SessionManager:
    """Manages interview sessions in-memory with thread safety."""

    def __init__(self, timeout_minutes=120):
        self._sessions = {}
        self._lock = threading.Lock()
        self._timeout = timedelta(minutes=timeout_minutes)

    def create_session(self, role, experience_level, user_id=None, cv_text=None, cv_filename=None, jd_text=None):
        """Create a new interview session and return its ID."""
        session_id = uuid.uuid4().hex[:16]
        session = {
            "id": session_id,
            "user_id": user_id,
            "role": role,
            "experience_level": experience_level,
            "cv_text": cv_text,
            "cv_filename": cv_filename,
            "jd_text": jd_text,
            "questions": [],
            "current_index": 0,
            "answers": [],
            "evaluations": [],
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._cleanup_expired()
            self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id):
        """Retrieve a session by ID. Returns None if not found or expired."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            created = datetime.fromisoformat(session["created_at"])
            if datetime.utcnow() - created > self._timeout:
                del self._sessions[session_id]
                return None
            return session.copy()

    def update_session(self, session_id, updates):
        """Update specific fields in a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            updates["updated_at"] = datetime.utcnow().isoformat()
            session.update(updates)
            return True

    def set_questions(self, session_id, questions):
        """Set the generated questions for a session."""
        return self.update_session(session_id, {
            "questions": questions,
            "status": "in_progress",
        })

    def submit_answer(self, session_id, answer, evaluation):
        """Record an answer and its evaluation, advance the question index."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session["answers"].append(answer)
            session["evaluations"].append(evaluation)
            session["current_index"] += 1
            session["updated_at"] = datetime.utcnow().isoformat()

            if session["current_index"] >= len(session["questions"]):
                session["status"] = "completed"

            return True

    def get_progress(self, session_id):
        """Get progress info for a session."""
        session = self.get_session(session_id)
        if session is None:
            return None
        return {
            "current": session["current_index"],
            "total": len(session["questions"]),
            "status": session["status"],
            "role": session["role"],
            "experience_level": session["experience_level"],
        }

    def _cleanup_expired(self):
        """Remove expired sessions. Must be called with lock held."""
        now = datetime.utcnow()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - datetime.fromisoformat(s["created_at"]) > self._timeout
        ]
        for sid in expired:
            del self._sessions[sid]

    def active_session_count(self):
        """Return the number of active sessions."""
        with self._lock:
            self._cleanup_expired()
            return len(self._sessions)
