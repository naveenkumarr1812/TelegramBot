import json
import os
import urllib.request

import streamlit as st
from database import supabase

st.set_page_config(page_title="Anime World Admin", page_icon="🎬", layout="wide")

st.title("🎬 Anime World Admin")
st.caption("Control panel for Anime resources, Telegram channel requirements, and Bot configuration.")
st.divider()


def count_rows(table: str) -> int:
    response = supabase.table(table).select("id").execute()
    return len(response.data or [])


def get_bot_status() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if not token:
        try:
            token = st.secrets.get("TELEGRAM_BOT_TOKEN") or st.secrets.get("BOT_TOKEN")
        except Exception:
            pass
    if not token:
        return "⚠️ Not Configured", "Configure in Bot Settings"
    try:
        url = f"https://api.telegram.org/bot{token.strip()}/getMe"
        req = urllib.request.Request(url, headers={"User-Agent": "AnimeWorldAdmin/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("ok"):
                username = data.get("result", {}).get("username", "Bot")
                return "🟢 Online", f"@{username}"
    except Exception:
        pass
    return "🔴 Offline", "Check Token"


try:
    resources = count_rows("resources")
    channels = count_rows("telegram_channels")
    users = count_rows("users")
    bot_status, bot_user = get_bot_status()
except Exception as exc:
    st.error(f"Database connection/query failed: {exc}")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Resources", resources)
c2.metric("Channels", channels)
c3.metric("Users", users)
c4.metric("Telegram Bot", bot_status, bot_user)

st.divider()
st.info(
    "💡 **Quick Navigation**:\n"
    "- **Resources**: Add and manage anime download links and channel lock rules.\n"
    "- **Channels**: Add and verify required Telegram channels.\n"
    "- **Bot Settings**: View and change the Telegram Bot API Key directly from the UI."
)
