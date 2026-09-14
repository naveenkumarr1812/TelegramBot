import asyncio
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import streamlit as st
from aiogram import Bot
from dotenv import load_dotenv
from supabase import Client, create_client

# ---------------------------------------------------------------------------
# Streamlit App Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Anime World Admin",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv(override=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# ---------------------------------------------------------------------------
# Database Client Initialization
# ---------------------------------------------------------------------------
SUPABASE_URL = None
SUPABASE_KEY = None

try:
    if "SUPABASE_URL" in st.secrets:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
    if "SUPABASE_KEY" in st.secrets:
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

if not SUPABASE_URL:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
if not SUPABASE_KEY:
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ `SUPABASE_URL` and `SUPABASE_KEY` are required in `.env` or Streamlit secrets.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def get_bot_token() -> str:
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
        return token.strip()

    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip(" '\"")
            if line.startswith("BOT_TOKEN="):
                return line.split("=", 1)[1].strip(" '\"")
    return ""


def check_telegram_bot(token: str) -> tuple[bool, dict | str]:
    """Validate bot token against Telegram's getMe API endpoint."""
    if not token or not token.strip():
        return False, "Token is empty."
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


def check_bot_channel_permission(chat_id: int) -> tuple[bool, str, dict | None]:
    """Test whether the configured bot can access the given channel and is an admin."""
    bot_token = get_bot_token()
    if not bot_token:
        return False, "Telegram Bot Token is not configured.", None

    async def _check():
        bot = Bot(token=bot_token)
        try:
            me = await bot.get_me()
            chat = await bot.get_chat(chat_id=chat_id)
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=me.id)
                status = getattr(member, "status", None)
                is_admin = status in ("administrator", "creator")
                return True, f"Connected to '{chat.title}' (Bot status: {status})", {
                    "title": chat.title,
                    "username": chat.username,
                    "is_admin": is_admin,
                    "status": status,
                    "bot_username": me.username,
                }
            except Exception as e:
                return False, f"Bot is not in the channel: {e}. Please add @{me.username} as an Administrator.", None
        except Exception as exc:
            return False, f"Cannot reach chat (chat_id={chat_id}): {exc}. Make sure @{bot_token[:10]}... is an Administrator in the channel.", None
        finally:
            await bot.session.close()

    return asyncio.run(_check())


def create_join_request_link(chat_id: int, name: str) -> str:
    """Generate a join-request invite link for a channel using Telegram Bot API."""
    bot_token = get_bot_token()
    if not bot_token:
        raise RuntimeError("Telegram Bot Token is missing. Configure it in Bot Settings.")

    async def _create():
        bot = Bot(token=bot_token)
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


def count_rows(table: str) -> int:
    response = supabase.table(table).select("id").execute()
    return len(response.data or [])


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
st.sidebar.title("🎬 Anime World")
st.sidebar.caption("Admin Management Panel")

selected_page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🎬 Anime Resources", "📢 Telegram Channels", "🤖 Bot Settings"],
    index=0,
)

current_bot_token = get_bot_token()
bot_username_env = os.getenv("BOT_USERNAME", "").strip().lstrip("@")


# ---------------------------------------------------------------------------
# Page 1: Dashboard
# ---------------------------------------------------------------------------
if selected_page == "📊 Dashboard":
    st.title("📊 Admin Dashboard")
    st.caption("Overview and real-time statistics for Anime World system.")
    st.divider()

    try:
        total_resources = count_rows("resources")
        total_channels = count_rows("telegram_channels")
        total_users = count_rows("users")
    except Exception as exc:
        st.error(f"Failed to fetch database counts: {exc}")
        total_resources = total_channels = total_users = 0

    bot_online = False
    bot_display = "Not Configured"
    bot_sub = "Configure in Bot Settings"

    if current_bot_token:
        is_valid, b_info = check_telegram_bot(current_bot_token)
        if is_valid and isinstance(b_info, dict):
            bot_online = True
            bot_display = "🟢 Online"
            bot_sub = f"@{b_info.get('username', 'Bot')}"
        else:
            bot_display = "🔴 Error"
            bot_sub = "Invalid Token"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Resources", total_resources)
    col2.metric("Telegram Channels", total_channels)
    col3.metric("Registered Users", total_users)
    col4.metric("Bot Status", bot_display, bot_sub)

    st.divider()
    st.subheader("🚀 Quick Actions & Guide")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        with st.container(border=True):
            st.markdown("### 🎬 Manage Resources")
            st.write("Add new anime download links and set required channel memberships.")
    with col_b:
        with st.container(border=True):
            st.markdown("### 📢 Manage Channels")
            st.write("Configure Telegram channels and automatic join-request invite links.")
    with col_c:
        with st.container(border=True):
            st.markdown("### 🤖 Bot Configuration")
            st.write("View connection health and update the Telegram Bot API token live.")


# ---------------------------------------------------------------------------
# Page 2: Anime Resources
# ---------------------------------------------------------------------------
elif selected_page == "🎬 Anime Resources":
    st.title("🎬 Anime Resources")
    st.caption("Create resources and generate Telegram deep links. Files remain stored on Google Drive.")
    st.divider()

    # Determine bot username for link generation
    active_bot_username = bot_username_env
    if not active_bot_username and current_bot_token:
        ok, info = check_telegram_bot(current_bot_token)
        if ok and isinstance(info, dict):
            active_bot_username = info.get("username", "")

    if not active_bot_username:
        st.warning("⚠️ Bot username not detected. Configure Bot Settings or set `BOT_USERNAME` in `.env`.")

    try:
        channel_rows = supabase.table("telegram_channels").select("id,name").eq("is_active", True).order("name").execute().data or []
    except Exception as exc:
        st.error(f"Failed to load channels: {exc}")
        channel_rows = []

    st.subheader("➕ Add New Resource")
    with st.form("add_resource_form"):
        name = st.text_input("Anime / Resource Name", placeholder="Example: Solo Leveling S01 — Complete Series")
        drive_url = st.text_input("Google Drive Link", placeholder="https://drive.google.com/...")
        options = {f"{row['name']} (ID {row['id']})": row['id'] for row in channel_rows}
        selected = st.multiselect("Required Channels", list(options), help="Users must join all selected channels to unlock download.")
        active = st.checkbox("Resource is active", True)
        submitted = st.form_submit_button("➕ Create Resource", use_container_width=True)

    if submitted:
        name = name.strip()
        drive_url = drive_url.strip()
        if not name:
            st.error("Please enter a resource name.")
        elif not drive_url:
            st.error("Please enter the Google Drive link.")
        elif not selected:
            st.error("Please select at least one required channel.")
        else:
            try:
                duplicate = supabase.table("resources").select("id").eq("name", name).limit(1).execute()
                if duplicate.data:
                    st.warning("A resource with this name already exists.")
                else:
                    created = supabase.table("resources").insert({
                        "name": name,
                        "drive_url": drive_url,
                        "is_active": active,
                    }).execute()
                    if not created.data:
                        raise RuntimeError("Supabase did not return the new resource.")
                    rid = created.data[0]["id"]
                    rows = [{"resource_id": rid, "channel_id": options[label]} for label in selected]
                    try:
                        supabase.table("resource_required_channels").insert(rows).execute()
                    except Exception:
                        supabase.table("resources").delete().eq("id", rid).execute()
                        raise
                    st.success("🎉 Resource created successfully!")
                    if active_bot_username:
                        st.code(f"https://t.me/{active_bot_username}?start=resource_{rid}")
                    st.rerun()
            except Exception as exc:
                st.error(f"Failed to create resource: {exc}")

    st.divider()
    st.subheader("📋 Existing Resources")
    try:
        resources = supabase.table("resources").select("*").order("created_at", desc=True).execute().data or []
    except Exception as exc:
        st.error(f"Failed to load resources: {exc}")
        resources = []

    if not resources:
        st.info("No resources created yet.")

    for resource in resources:
        rid = resource["id"]
        is_res_active = resource.get("is_active", True)
        bot_link = f"https://t.me/{active_bot_username}?start=resource_{rid}" if active_bot_username else None

        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"### 🎬 {resource.get('name', 'Unnamed Resource')}")
            c2.write("🟢 **Active**" if is_res_active else "🔴 **Inactive**")
            st.write(f"**Resource ID**: `{rid}`")
            st.write("**Google Drive Link**")
            st.code(resource.get("drive_url") or "Not configured")
            st.write("**Telegram Deep Link**")
            st.code(bot_link or "Bot username required to generate link")

            try:
                required = supabase.table("resource_required_channels").select("channel_id, telegram_channels(name)").eq("resource_id", rid).execute().data or []
                names = []
                for row in required:
                    channel = row.get("telegram_channels")
                    if isinstance(channel, list):
                        channel = channel[0] if channel else None
                    if channel:
                        names.append(channel.get("name", "Unnamed Channel"))
                st.write("**Required Channels:** " + (", ".join(names) if names else "None"))
            except Exception as exc:
                st.warning(f"Could not load required channels: {exc}")

            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("⛔ Disable" if is_res_active else "✅ Enable", key=f"toggle_res_{rid}", use_container_width=True):
                supabase.table("resources").update({"is_active": not is_res_active}).eq("id", rid).execute()
                st.rerun()
            if btn_col2.button("🗑️ Delete", key=f"del_res_{rid}", use_container_width=True):
                try:
                    supabase.table("resource_required_channels").delete().eq("resource_id", rid).execute()
                except Exception:
                    pass
                supabase.table("resources").delete().eq("id", rid).execute()
                st.rerun()


# ---------------------------------------------------------------------------
# Page 3: Telegram Channels
# ---------------------------------------------------------------------------
elif selected_page == "📢 Telegram Channels":
    st.title("📢 Telegram Channels")
    st.caption("Manage channels users must join before unlocking resource links.")
    st.divider()

    st.info(
        "📌 **Important Setup Requirement**:\n"
        "1. Add your Telegram Bot as an **Administrator** in each channel you register below.\n"
        "2. Ensure the Bot has **'Invite Users via Link'** permission in the channel."
    )

    st.subheader("➕ Add New Channel")
    with st.form("add_channel_form"):
        ch_name = st.text_input("Channel Name", placeholder="Example: Anime World Updates")
        chat_id_text = st.text_input("Telegram Chat ID", placeholder="e.g. -1001234567890 (Channel ID with -100 prefix)")
        ch_username = st.text_input("Public Username (optional)", placeholder="@examplechannel")
        manual_link = st.text_input("Existing Invite Link (optional)", placeholder="Leave empty to auto-generate a join-request link")
        ch_submitted = st.form_submit_button("➕ Add Channel", use_container_width=True)

    if ch_submitted:
        ch_name = ch_name.strip()
        ch_username = ch_username.strip() or None
        manual_link = manual_link.strip() or None

        if not ch_name:
            st.error("Please enter a channel name.")
        else:
            try:
                chat_id = int(chat_id_text.strip())
            except ValueError:
                st.error("Chat ID must be an integer (e.g. -1001234567890).")
            else:
                try:
                    existing = supabase.table("telegram_channels").select("id").eq("chat_id", chat_id).limit(1).execute()
                    if existing.data:
                        st.warning("This channel is already configured in the database.")
                    else:
                        with st.spinner("Checking bot channel permissions..."):
                            ok, msg, details = check_bot_channel_permission(chat_id)

                        if not ok:
                            st.error(f"❌ {msg}")
                        else:
                            invite_link = manual_link
                            if not invite_link:
                                try:
                                    invite_link = create_join_request_link(chat_id, ch_name)
                                except Exception as err:
                                    st.error(f"Failed to generate join-request invite link: {err}")
                                    invite_link = None

                            if invite_link:
                                result = supabase.table("telegram_channels").insert({
                                    "name": ch_name,
                                    "chat_id": chat_id,
                                    "username": ch_username or (details.get("username") if details else None),
                                    "invite_link": invite_link,
                                    "is_active": True,
                                }).execute()
                                if result.data:
                                    st.success(f"🎉 Channel '{ch_name}' added successfully! (Bot Admin Status: Verified)")
                                    st.rerun()
                                st.error("Channel was not created in database.")
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
        st.info("No Telegram channels added yet.")

    for ch in channels:
        cid = ch["id"]
        ch_active = ch.get("is_active", True)
        chat_id_val = ch.get("chat_id")
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"### 📢 {ch.get('name', 'Unnamed Channel')}")
            c2.write("🟢 **Active**" if ch_active else "🔴 **Inactive**")
            st.write(f"**Chat ID**: `{chat_id_val}`")
            st.write(f"**Username**: `{ch.get('username') or '—'}`")
            if ch.get("invite_link"):
                st.write("**Invite / Join Request Link**")
                st.code(ch["invite_link"])

            test_col, b_col1, b_col2 = st.columns([2, 1, 1])
            if test_col.button("🔍 Check Bot Permissions", key=f"test_ch_{cid}", use_container_width=True):
                if chat_id_val:
                    with st.spinner("Testing bot access to channel..."):
                        t_ok, t_msg, t_det = check_bot_channel_permission(chat_id_val)
                    if t_ok:
                        st.success(f"✅ {t_msg}")
                    else:
                        st.error(f"❌ {t_msg}")
            if b_col1.button("⛔ Disable" if ch_active else "✅ Enable", key=f"toggle_ch_{cid}", use_container_width=True):
                supabase.table("telegram_channels").update({"is_active": not ch_active}).eq("id", cid).execute()
                st.rerun()
            if b_col2.button("🗑️ Delete", key=f"del_ch_{cid}", use_container_width=True):
                try:
                    supabase.table("resource_required_channels").delete().eq("channel_id", cid).execute()
                except Exception:
                    pass
                supabase.table("telegram_channels").delete().eq("id", cid).execute()
                st.rerun()


# ---------------------------------------------------------------------------
# Page 4: Bot Settings
# ---------------------------------------------------------------------------
elif selected_page == "🤖 Bot Settings":
    st.title("🤖 Telegram Bot Settings")
    st.caption("Manage and update your Telegram Bot API token directly from the admin panel.")
    st.divider()

    st.subheader("Current Bot Status")
    if current_bot_token:
        is_valid, bot_info = check_telegram_bot(current_bot_token)
        if is_valid and isinstance(bot_info, dict):
            col1, col2, col3 = st.columns(3)
            col1.metric("Connection", "🟢 Connected")
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
    st.subheader("Update Bot API Key")
    st.write(
        "Enter a new Telegram Bot API token generated from "
        "[**@BotFather**](https://t.me/BotFather) on Telegram."
    )

    with st.form("update_bot_token_form"):
        new_token_input = st.text_input(
            "New Bot API Token",
            type="password",
            placeholder="e.g. 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            help="Paste the bot token from @BotFather here.",
        )
        token_submitted = st.form_submit_button("🔍 Test & Save New Bot Token", use_container_width=True)

    if token_submitted:
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
                        f"📌 *Note: If the bot worker process is running in the background, restart it to reload the new token.*"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update `.env` file: {e}")
            else:
                st.error(f"❌ Telegram API rejected this token: {info}")
