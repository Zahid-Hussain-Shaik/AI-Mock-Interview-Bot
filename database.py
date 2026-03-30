"""
SQLite database initialization and connection helpers.
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interview_bot.db")


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def close_db(conn):
    """Close a database connection."""
    if conn:
        conn.close()


def init_db():
    """Initialize the database with required tables."""
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS interviews (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                experience_level TEXT NOT NULL,
                cv_filename TEXT,
                cv_text TEXT,
                jd_text TEXT,
                questions TEXT,
                answers TEXT,
                evaluations TEXT,
                status TEXT DEFAULT 'in_progress',
                average_score REAL,
                total_questions INTEGER DEFAULT 0,
                answered_questions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_interviews_user_id ON interviews(user_id);
            CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
        """)
        conn.commit()
        logger.info("Database initialized successfully at %s", DATABASE_PATH)
    finally:
        close_db(conn)
