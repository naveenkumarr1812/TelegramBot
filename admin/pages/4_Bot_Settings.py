import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="Bot Settings - Anime World Admin", page_icon="🤖", layout="wide")

load_dotenv(override=True)

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def get_current_token() -> str:
    """Retrieve current Telegram bot token from secrets, environment, or .env."""
    try:
        if "TELEGRAM_BOT_TOKEN" in st.secrets:
            return st.secrets["TELEGRAM_BOT_TOKEN"]
        if "BOT_TOKEN" in st.secrets:
            return st.secrets["BOT_TOKEN"]
    except Exception:
        pass

    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if token:
        return token

    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip(" '\"")
            if line.startswith("BOT_TOKEN="):
                return line.split("=", 1)[1].strip(" '\"")
    return ""


def check_telegram_bot(token: str) -> tuple[bool, dict | str]:
    """Test the bot token against Telegram's getMe API endpoint."""
    if not token or not token.strip():
        return False, "Token cannot be empty."

    token = token.strip()
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AnimeWorldAdmin/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("ok"):
                return True, data.get("result", {})
            return False, data.get("description", "Unknown Telegram API error.")
    except urllib.error.HTTPError as err:
        try:
            err_body = json.loads(err.read().decode("utf-8"))
            return False, err_body.get("description", f"HTTP Error {err.code}")
        except Exception:
            return False, f"Telegram API Error: {err}"
    except Exception as exc:
        return False, f"Connection failed: {exc}"


def update_env_file(new_token: str) -> None:
    """Safely update or add TELEGRAM_BOT_TOKEN in .env file."""
    new_token = new_token.strip()
    lines = []
    found = False

    if ENV_PATH.exists():
        raw_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        for line in raw_lines:
            stripped = line.strip()
            if stripped.startswith("TELEGRAM_BOT_TOKEN=") or stripped.startswith("BOT_TOKEN="):
                if not found:
                    lines.append(f'TELEGRAM_BOT_TOKEN="{new_token}"')
                    found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f'TELEGRAM_BOT_TOKEN="{new_token}"')

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ["TELEGRAM_BOT_TOKEN"] = new_token
    load_dotenv(override=True)


st.title("🤖 Telegram Bot Settings")
st.caption("Manage and update your Telegram Bot API token directly from the admin panel.")
st.divider()

current_token = get_current_token()

# Section 1: Current Bot Status
st.subheader("Current Bot Status")
if current_token:
    is_valid, bot_info = check_telegram_bot(current_token)
    if is_valid and isinstance(bot_info, dict):
        col1, col2, col3 = st.columns(3)
        col1.metric("Status", "🟢 Connected")
        col2.metric("Bot Username", f"@{bot_info.get('username', 'N/A')}")
        col3.metric("Bot ID", str(bot_info.get("id", "N/A")))

        st.success(
            f"**Active Bot**: `{bot_info.get('first_name', 'Bot')}` "
            f"([@{bot_info.get('username')}](https://t.me/{bot_info.get('username')}))"
        )
    else:
        st.error(f"🔴 Current token is invalid or unreachable: {bot_info}")
else:
    st.warning("⚠️ No Telegram Bot API token is currently configured.")

st.divider()

# Section 2: Change / Update Bot API Token
st.subheader("Update Bot API Key")
st.write(
    "Enter a new Telegram Bot API token generated from "
    "[**@BotFather**](https://t.me/BotFather) on Telegram."
)

with st.form("update_bot_token_form"):
    masked_placeholder = ("•" * 20 + current_token[-6:]) if len(current_token) > 10 else ""
    new_token_input = st.text_input(
        "New Bot API Token",
        type="password",
        placeholder="e.g. 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
        help="Paste the bot token from @BotFather here.",
    )
    submitted = st.form_submit_button("🔍 Test & Save New Bot Token", use_container_width=True)

if submitted:
    if not new_token_input.strip():
        st.error("Please enter a valid bot token.")
    else:
        token_to_test = new_token_input.strip()
        with st.spinner("Testing token with Telegram API..."):
            valid, info = check_telegram_bot(token_to_test)

        if valid and isinstance(info, dict):
            try:
                update_env_file(token_to_test)
                st.success(
                    f"✅ **Token successfully updated and saved!**\n\n"
                    f"- **Bot Name**: {info.get('first_name')}\n"
                    f"- **Username**: @{info.get('username')}\n"
                    f"- **Bot ID**: `{info.get('id')}`\n\n"
                    f"📌 *Note: If the Telegram bot background worker is running, restart it to reload the new bot token.*"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update .env file: {e}")
        else:
            st.error(f"❌ Telegram API rejected this token: {info}")
