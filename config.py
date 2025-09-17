import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()


class Config:
    """Central configuration for Flask application."""

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:Bala123@localhost:5432/budget_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")

    # Frontend / CORS
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    # Flask run settings
    FLASK_RUN_HOST = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    FLASK_RUN_PORT = int(os.environ.get("FLASK_RUN_PORT", 5000))
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")