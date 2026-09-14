import asyncio
import os

import streamlit as st
from aiogram import Bot
from database import supabase
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

st.set_page_config(page_title="Channels | Anime World", page_icon="📢", layout="wide")
st.title("📢 Telegram Channels")
st.caption("Manage the channels users must join before a resource is released.")
st.divider()


def create_join_request_link(chat_id: int, name: str) -> str:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing from .env")

    async def _create():
        bot = Bot(token=BOT_TOKEN)
        try:
            invite = await bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"AnimeWorld - {name}"[:32],
                creates_join_request=True,
            )
            return invite.invite_link
        finally:
            await bot.session.close()

    return asyncio.run(_create())


st.subheader("➕ Add New Channel")
with st.form("add_channel_form"):
    name = st.text_input("Channel Name", placeholder="Example: Anime World Updates")
    chat_id_text = st.text_input("Telegram Chat ID", placeholder="-1001234567890")
    username = st.text_input("Public Username (optional)", placeholder="@examplechannel")
    manual_link = st.text_input(
        "Existing Invite Link (optional)",
        placeholder="Leave empty to generate a join-request link",
    )
    submitted = st.form_submit_button("➕ Add Channel", use_container_width=True)

if submitted:
    name = name.strip()
    username = username.strip() or None
    manual_link = manual_link.strip() or None
    if not name:
        st.error("Please enter a channel name.")
    else:
        try:
            chat_id = int(chat_id_text.strip())
        except ValueError:
            st.error("Chat ID must be a number, e.g. -1001234567890.")
        else:
            try:
                existing = supabase.table("telegram_channels").select("id").eq("chat_id", chat_id).limit(1).execute()
                if existing.data:
                    st.warning("This channel is already configured.")
                else:
                    invite_link = manual_link
                    if not invite_link:
                        invite_link = create_join_request_link(chat_id, name)
                    result = supabase.table("telegram_channels").insert({
                        "name": name,
                        "chat_id": chat_id,
                        "username": username,
                        "invite_link": invite_link,
                        "is_active": True,
                    }).execute()
                    if result.data:
                        st.success("Channel added successfully.")
                        st.rerun()
                    st.error("Channel was not created.")
            except Exception as exc:
                st.error(f"Failed to add channel: {exc}")

st.divider()
st.subheader("📋 Existing Channels")
try:
    response = supabase.table("telegram_channels").select("*").order("created_at", desc=True).execute()
    channels = response.data or []
except Exception as exc:
    st.error(f"Failed to load channels: {exc}")
    channels = []

if not channels:
    st.info("No Telegram channels have been added yet.")

for channel in channels:
    cid = channel["id"]
    active = channel.get("is_active", True)
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"### 📢 {channel.get('name', 'Unnamed Channel')}")
        c2.write("**Active**" if active else "**Inactive**")
        st.write(f"Chat ID: `{channel.get('chat_id')}`")
        st.write(f"Username: `{channel.get('username') or '—'}`")
        if channel.get("invite_link"):
            st.code(channel["invite_link"])
        a, b = st.columns(2)
        if a.button("⛔ Disable" if active else "✅ Enable", key=f"toggle_{cid}", use_container_width=True):
            supabase.table("telegram_channels").update({"is_active": not active}).eq("id", cid).execute()
            st.rerun()
        if b.button("🗑️ Delete", key=f"delete_{cid}", use_container_width=True):
            try:
                supabase.table("resource_required_channels").delete().eq("channel_id", cid).execute()
            except Exception:
                pass
            supabase.table("telegram_channels").delete().eq("id", cid).execute()
            st.rerun()
