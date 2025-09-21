import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def normalize_db_url(url: str) -> str:
    """
    Normalize DATABASE_URL for SQLAlchemy.
    - Some services give postgres://
    - SQLAlchemy needs postgresql+psycopg2://
    """
    if not url:
        return None
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

class Config:
    SQLALCHEMY_DATABASE_URI = normalize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
