import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / ".env", override=False)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # Default to a writable, ephemeral SQLite path (/tmp) for cloud deploys; override with DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:////tmp/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(base_dir / "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    # Admin credentials
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "FractalAdmin@123")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Fractalisadmin123")

    # Excel export path
    EXCEL_OUTPUT_PATH = os.getenv(
        "EXCEL_OUTPUT_PATH",
        "/var/data/base.xlsx",
    )
    PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "https://vornato.github.io/Fractal")
    PASSWORD_RESET_URL_BASE = os.getenv("PASSWORD_RESET_URL_BASE", f"{PUBLIC_SITE_URL}/register.html")
    PASSWORD_RESET_TOKEN_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_MINUTES", "60"))

    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    # Cookie settings: default to Lax so cookies survive 127.0.0.1:5000 <-> 127.0.0.1:5500 without requiring HTTPS
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    _raw_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    if _raw_samesite.lower() == "none" and not SESSION_COOKIE_SECURE:
        # Browsers reject SameSite=None when Secure is false (HTTP), so fallback to Lax for local dev
        SESSION_COOKIE_SAMESITE = "Lax"
    else:
        SESSION_COOKIE_SAMESITE = _raw_samesite
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://127.0.0.1:5500")
    EXTRA_CORS_ORIGINS = _split_csv(
        os.getenv(
            "EXTRA_CORS_ORIGINS",
            "http://localhost:5500,https://vornato.github.io",
        )
    )

