# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# ✅ Load .env for local development
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _normalize_db_url(url: str) -> str:
    """
    Ensure DATABASE_URL works with SQLAlchemy.
    Render gives postgres://, but SQLAlchemy needs postgresql+psycopg2://
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


class Config:
    """Base configuration shared across environments."""

    # 🔑 Security
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    # 🌍 Environment
    APP_ENV = os.getenv("APP_ENV", "development").lower()

    # 🗄️ Database
    if APP_ENV == "development":
        # Local fallback (your pgAdmin Postgres)
        _raw_db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:Bala123@localhost:5432/budget_db"
        )
    else:
        # Production (Render)
        _raw_db_url = os.getenv("DATABASE_URL")
        if not _raw_db_url:
            raise ValueError("❌ DATABASE_URL is required in production")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(_raw_db_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📡 CORS
    CORS_HEADERS = "Content-Type"
    FRONTEND_URLS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://aibudgettracker.netlify.app",
    ]

    # 📧 Mail (optional, reports/alerts)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("1", "true", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

    # ⏱️ Scheduler
    SCHEDULER_API_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
