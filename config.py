"""
Application configuration module.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-abc123")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    # Interview settings
    MIN_QUESTIONS = int(os.getenv("MIN_QUESTIONS", "8"))
    MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", "12"))
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "120"))
    SESSION_TYPE = "filesystem"
    
    # API settings
    CLAUDE_MAX_RETRIES = int(os.getenv("CLAUDE_MAX_RETRIES", "3"))
    CLAUDE_TIMEOUT_SECONDS = int(os.getenv("CLAUDE_TIMEOUT_SECONDS", "45"))
    CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

    # File upload settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

    # Debug
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


def get_config():
    """Return the appropriate config based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    return configs.get(env, DevelopmentConfig)
