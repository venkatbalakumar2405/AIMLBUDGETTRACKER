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

    # Normalize DB URI (postgres:// → postgresql+psycopg2://)
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )

        # Ensure SSL is enforced (important for Neon/Render)
        if "sslmode=" not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///budget_dev.db"

    # Logging
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_FILE = os.getenv("LOG_FILE", "budget_tracker.log")

    # Auto-create tables (optional, useful for dev only)
    AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "false")

    # Frontend CORS origins
    FRONTEND_URLS = os.getenv("FRONTEND_URLS")

    # Mail (if you use Flask-Mail)
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
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = Config.DATABASE_URL
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("❌ DATABASE_URL must be set for production.")


# Default export for Flask CLI
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
)
