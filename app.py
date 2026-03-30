"""
AI Mock Interview Bot — Flask Application
"""

import logging
from flask import Flask, render_template, jsonify, session, redirect, g

from config import get_config
from database import init_db
from models.user import get_user_by_id
from services.claude_client import ClaudeClient
from services.session_manager import SessionManager
from routes.interview import interview_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    cfg = get_config()
    app.config.from_object(cfg)
    
    # Initialize database
    with app.app_context():
        init_db()

    # Initialize services
    try:
        claude_client = ClaudeClient(
            api_key=cfg.ANTHROPIC_API_KEY,
            model=cfg.CLAUDE_MODEL,
            max_retries=cfg.CLAUDE_MAX_RETRIES,
            timeout=cfg.CLAUDE_TIMEOUT_SECONDS,
            max_tokens=cfg.CLAUDE_MAX_TOKENS,
        )
        app.config["CLAUDE_CLIENT"] = claude_client
        logger.info("Claude client initialized (model=%s)", cfg.CLAUDE_MODEL)
    except ValueError as e:
        logger.warning("Claude client not initialized: %s", str(e))
        app.config["CLAUDE_CLIENT"] = None

    session_manager = SessionManager(timeout_minutes=cfg.SESSION_TIMEOUT_MINUTES)
    app.config["SESSION_MANAGER"] = session_manager

    # Register blueprints
    app.register_blueprint(interview_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    # Middleware to load user
    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        if user_id is None:
            g.user = None
        else:
            g.user = get_user_by_id(user_id)

    # Page routes
    @app.route("/")
    def index():
        return render_template("index.html")
        
    @app.route("/login")
    def login_page():
        if g.user:
            return redirect("/dashboard")
        return render_template("login.html")

    @app.route("/signup")
    def signup_page():
        if g.user:
            return redirect("/dashboard")
        return render_template("signup.html")
        
    @app.route("/dashboard")
    def dashboard_page():
        if not g.user:
            return redirect("/login")
        return render_template("dashboard.html")

    @app.route("/interview/<session_id>")
    def interview_page(session_id):
        if not g.user:
            return redirect("/login")
        return render_template("interview.html", session_id=session_id)

    @app.route("/results/<session_id>")
    def results_page(session_id):
        if not g.user:
            return redirect("/login")
        return render_template("results.html", session_id=session_id)

    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "success": False,
            "data": None,
            "error": {"code": "BAD_REQUEST", "message": str(e)},
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({
            "success": False,
            "data": None,
            "error": {"code": "UNAUTHORIZED", "message": "Authentication required."},
        }), 401
        
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Resource not found."},
        }), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error("Internal server error: %s", str(e))
        return jsonify({
            "success": False,
            "data": None,
            "error": {"code": "SERVER_ERROR", "message": "An internal error occurred."},
        }), 500

    logger.info("AI Mock Interview Bot initialized successfully")
    return app


# Entry point
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", True))
