import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = bool(os.getenv("VERCEL")) or not os.access(BASE_DIR, os.W_OK)
TMP_DIR = Path(os.getenv("TMPDIR", "/tmp"))


class Config:
    IS_VERCEL = IS_VERCEL
    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32)
    _database_url = os.getenv("DATABASE_URL")
    if _database_url and _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url or f"sqlite:///{(TMP_DIR if IS_VERCEL else BASE_DIR / 'database') / 'shopping.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH") or 5 * 1024 * 1024)
    UPLOAD_FOLDER = (TMP_DIR / "uploads") if IS_VERCEL else (BASE_DIR / "static" / "uploads")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"

