import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Config:
    """Base configuration shared across environments."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = os.getenv("DATABASE_URL")

    # ✅ Normalize DB URI (postgres:// → postgresql+psycopg2://)
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://", "postgresql+psycopg2://", 1
        )

    # ✅ Ensure Neon/Postgres works with psycopg2
    if DATABASE_URL:
        # Fix invalid channel_binding issue
        if "channel_binding=require" in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace(
                "channel_binding=require", "gssencmode=disable"
            )

        # Force sslmode=require if missing
        if "sslmode=" not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require&gssencmode=disable"
        # Ensure gssencmode=disable is always present
        elif "gssencmode=" not in DATABASE_URL:
            DATABASE_URL += "&gssencmode=disable"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///budget_dev.db"

    # Logging
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_FILE = os.getenv("LOG_FILE", "budget_tracker.log")

    # Auto-create tables (optional, dev only)
    AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "false")

    # Frontend CORS origins
    FRONTEND_URLS = os.getenv("FRONTEND_URLS")

    # Mail (if Flask-Mail is enabled)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config.DATABASE_URL or "sqlite:///budget_dev.db"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = Config.DATABASE_URL


# ✅ Map for easy lookup
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
)
