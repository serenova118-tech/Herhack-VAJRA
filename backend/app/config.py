import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


HIBP_API_KEY = os.getenv("HIBP_API_KEY", "").strip()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
# Model names change over time. Run `python check_models.py` to list the models
# your key can actually use, then set GEMINI_MODEL in backend/.env.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

# Comma-separated list of browser origins allowed to call this API.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "VAJRA_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]

MAX_UPLOAD_BYTES = _int_env("VAJRA_MAX_UPLOAD_MB", 10) * 1024 * 1024

