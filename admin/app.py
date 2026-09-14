import streamlit as st
from database import supabase

st.set_page_config(page_title="Anime World Admin", page_icon="🎬", layout="wide")

st.title("🎬 Anime World Admin")
st.caption("Control panel for resources and Telegram channel requirements.")
st.divider()


def count_rows(table: str) -> int:
    response = supabase.table(table).select("id").execute()
    return len(response.data or [])

try:
    resources = count_rows("resources")
    channels = count_rows("telegram_channels")
    users = count_rows("users")
except Exception as exc:
    st.error(f"Database connection/query failed: {exc}")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Resources", resources)
c2.metric("Channels", channels)
c3.metric("Users", users)

st.info("Use the pages in the sidebar to manage Resources and Telegram Channels.")
