# config.py
import os
import logging
from dotenv import load_dotenv

# Load local .env file (ignored in production)
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Config")


def _normalize_db_url(url: str) -> str:
    """
    Render sometimes provides DATABASE_URL starting with 'postgres://'
    SQLAlchemy requires 'postgresql+psycopg2://'
    """
    if not url:
        return None
    if url.startswith("postgres://"):
        fixed_url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        logger.info("✅ Normalized DATABASE_URL from 'postgres://' → 'postgresql+psycopg2://'")
        return fixed_url
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_HEADERS = "Content-Type"

    # Mail (optional, for notifications/reports)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

    # APScheduler
    SCHEDULER_API_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    _raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:Bala123@localhost:5432/budget_db",
    )
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(_raw_db_url)
    logger.info(f"🛠 Development DB: {SQLALCHEMY_DATABASE_URI}")


class TestingConfig(Config):
    TESTING = True
    _raw_db_url = os.getenv(
        "DATABASE_TEST_URL",
        "postgresql+psycopg2://postgres:Bala123@localhost:5432/budget_test_db",
    )
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(_raw_db_url)
    logger.info(f"🧪 Testing DB: {SQLALCHEMY_DATABASE_URI}")


class ProductionConfig(Config):
    DEBUG = False
    _raw_db_url = os.getenv("DATABASE_URL")
    if not _raw_db_url:
        raise ValueError("❌ DATABASE_URL is required in production")
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(_raw_db_url)
    logger.info(f"🚀 Production DB: {SQLALCHEMY_DATABASE_URI}")
