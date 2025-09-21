# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # ✅ Load .env for local dev

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_db_url(url: str) -> str:
    """
    Render sometimes provides DATABASE_URL starting with 'postgres://'
    SQLAlchemy requires 'postgresql+psycopg2://'
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    # ✅ Choose database based on environment
    APP_ENV = os.getenv("APP_ENV", "development")

    if APP_ENV == "development":
        # Local DB (fallback)
        _raw_db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:Bala123@localhost:5432/budget_db"
        )
    else:
        # Production (Render must always use DATABASE_URL)
        _raw_db_url = os.getenv("DATABASE_URL")
        if not _raw_db_url:
            raise ValueError("❌ DATABASE_URL is required in production")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(_raw_db_url)

    # Other configs
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_HEADERS = "Content-Type"

    # Mail (optional, for notifications/reports)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-password")

    # APScheduler
    SCHEDULER_API_ENABLED = True
