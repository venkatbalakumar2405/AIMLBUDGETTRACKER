import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class Config:
    """Central configuration for Flask application."""

    # ================== DATABASE ==================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/budgettracker"  # ✅ safe default
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ================== SECURITY ==================
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    # ================== FRONTEND / CORS ==================
    # Supports multiple origins (comma-separated in .env)
    _frontend_urls = os.getenv(
        "FRONTEND_URLS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    FRONTEND_URLS = [url.strip() for url in _frontend_urls.split(",") if url.strip()]

    # ================== SERVER SETTINGS ==================
    FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    FLASK_RUN_PORT = int(os.getenv("FLASK_RUN_PORT", 5000))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

    # ================== LOGGING ==================
    LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
    LOG_FILE = os.getenv("LOG_FILE", "budget_tracker.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))  # 5 MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

    @classmethod
    def ensure_log_dir(cls):
        """Ensure the log directory exists."""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    FLASK_DEBUG = False