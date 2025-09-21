import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    """Helper to parse boolean env vars safely."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Central configuration for Flask application."""

    # ================== DATABASE ================== #
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:Bala123@localhost:5432/budget_db"  # ✅ local default
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ================== SECURITY ================== #
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    # ================== FRONTEND / CORS ================== #
    # Supports multiple origins (comma-separated in .env)
    _frontend_urls = os.getenv(
        "FRONTEND_URLS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    FRONTEND_URLS: list[str] = [
        url.strip() for url in _frontend_urls.split(",") if url.strip()
    ]

    # Always include Netlify deploy as a safe fallback
    if "https://aibudgettracker.netlify.app" not in FRONTEND_URLS:
        FRONTEND_URLS.append("https://aibudgettracker.netlify.app")

    # ================== SERVER SETTINGS ================== #
    FLASK_RUN_HOST: str = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    FLASK_RUN_PORT: int = int(os.getenv("FLASK_RUN_PORT", 5000))
    FLASK_DEBUG: bool = _get_bool("FLASK_DEBUG", False)

    # ================== LOGGING ================== #
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "logs"))
    LOG_FILE: str = os.getenv("LOG_FILE", "budget_tracker.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))  # 5 MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", 5))

    @classmethod
    def ensure_log_dir(cls) -> None:
        """Ensure the log directory exists early in app startup."""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        """Factory: return appropriate config class based on APP_ENV."""
        env = os.getenv("APP_ENV", "development").lower()
        if env == "production":
            return ProductionConfig()
        if env == "testing":
            return TestingConfig()
        return DevelopmentConfig()


class DevelopmentConfig(Config):
    DEBUG: bool = True
    TESTING: bool = False


class TestingConfig(Config):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(Config):
    DEBUG: bool = False
    TESTING: bool = False
    FLASK_DEBUG: bool = False