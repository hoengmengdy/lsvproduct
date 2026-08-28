import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'database' / 'shopping.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"

