# config.py
import os
import logging
from dotenv import load_dotenv

# Load local .env (ignored in production)
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

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

    # ✅ Choose database based on environment
    APP_ENV = os.getenv("APP_ENV", "development")

    if APP_ENV == "development":
        # Local DB (fallback if DATABASE_URL not set)
        _raw_db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:Bala123@localhost:5432/budget_db",
        )
    else:
        # Production (Render must always provide DATABASE_URL)
        _raw_db_url = os.getenv("DATABASE_URL")
        if not _raw_db_url:
            raise ValueError("❌ DATABASE_URL is required in production")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(_raw_db_url)

    # Mask password in logs but still print useful debug info
    if SQLALCHEMY_DATABASE_URI:
        safe_uri = SQLALCHEMY_DATABASE_URI.replace(
            SQLALCHEMY_DATABASE_URI.split(":")[2].split("@")[0], "*****"
        )
        logger.info(f"🔗 Using database: {safe_uri}")
    else:
        logger.error("❌ No DATABASE_URL provided. Cannot connect to database.")

    # Other configs
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