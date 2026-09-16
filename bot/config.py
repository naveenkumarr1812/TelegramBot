import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

ENV_PATH = BOT_DIR.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or "").strip().strip("'\"")
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip().strip("'\"")
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip().strip("'\"")
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "").strip().strip("'\"").lstrip("@")


def validate_config() -> None:
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if missing:
        raise RuntimeError(
            "Missing environment variable(s): " + ", ".join(missing)
        )


validate_config()


def get_active_bot_token() -> str:
    """
    Retrieve Telegram bot token:
    1. Checks Supabase `bot_settings` table (key: 'telegram_bot_token').
    2. Falls back to environment variable TELEGRAM_BOT_TOKEN / BOT_TOKEN.
    """
    try:
        from database import get_setting
        db_token = get_setting("telegram_bot_token")
        if db_token and db_token.strip():
            return db_token.strip()
    except Exception:
        pass

    env_token = (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or "").strip().strip("'\"")
    return env_token


def get_active_bot_username() -> str:
    """Retrieve active bot username from Supabase settings or environment."""
    try:
        from database import get_setting
        db_username = get_setting("bot_username")
        if db_username and db_username.strip():
            return db_username.strip().lstrip("@")
    except Exception:
        pass

    return BOT_USERNAME

