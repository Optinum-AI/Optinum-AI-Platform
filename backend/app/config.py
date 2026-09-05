import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = 60 * 24

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
try:
    OLLAMA_TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT_S", "90"))
except ValueError:
    OLLAMA_TIMEOUT_S = 90.0

DB_PATH = DATA_DIR / "optimum.db"

OAUTH_REDIRECT_BASE = os.environ.get(
    "OAUTH_REDIRECT_BASE",
    "http://localhost:8000"
)

FRONTEND_BASE = os.environ.get(
    "FRONTEND_BASE",
    "http://localhost:5173"
)

SOCIAL_CREDS = {
    "google": (
        os.environ.get("GOOGLE_CLIENT_ID", ""),
        os.environ.get("GOOGLE_CLIENT_SECRET", "")
    ),
    "x": (
        os.environ.get("X_CLIENT_ID", ""),
        os.environ.get("X_CLIENT_SECRET", "")
    ),
    "linkedin": (
        os.environ.get("LINKEDIN_CLIENT_ID", ""),
        os.environ.get("LINKEDIN_CLIENT_SECRET", "")
    ),
    "facebook": (
        os.environ.get("META_APP_ID", ""),
        os.environ.get("META_APP_SECRET", "")
    ),
    "instagram": (
        os.environ.get("META_APP_ID", ""),
        os.environ.get("META_APP_SECRET", "")
    ),
    "youtube": (
        os.environ.get("GOOGLE_CLIENT_ID", ""),
        os.environ.get("GOOGLE_CLIENT_SECRET", "")
    ),
    "tiktok": (
        os.environ.get("TIKTOK_CLIENT_KEY", ""),
        os.environ.get("TIKTOK_CLIENT_SECRET", "")
    ),
    "discord": (
        os.environ.get("DISCORD_WEBHOOK_URL", ""),
        "webhook"
    ),
}