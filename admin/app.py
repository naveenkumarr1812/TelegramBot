import asyncio
import hashlib
import json
import os
import secrets
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
    page_title="Anime World — Admin",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------
# A flat, hairline-bordered "operations console" look: near-black canvas,
# a single restrained amber accent reserved for status/primary actions,
# no shadows, no gradients, one deliberate corner radius throughout.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root{
    --canvas:#0c0d0f;
    --panel:#151719;
    --panel-alt:#1a1d20;
    --line:#292c30;
    --line-strong:#3a3e43;
    --ink:#e8e9eb;
    --ink-mid:#9aa0a6;
    --ink-low:#666b71;
    --amber:#d3a625;
    --amber-ink:#191204;
    --good:#5aab7c;
    --bad:#c96b6b;
    --radius:5px;
}

html, body, [class*="css"]{
    font-family:'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
code, .stCodeBlock, .aw-mono{
    font-family:'IBM Plex Mono', ui-monospace, monospace !important;
}

.stApp{ background: var(--canvas) !important; color: var(--ink); }
.block-container{ padding-top: 5.5rem; padding-bottom: 3rem; max-width: 1180px; }

/* ---- Sidebar / rail ---- */
section[data-testid="stSidebar"]{
    background: var(--panel) !important;
    border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] > div{ padding-top: 1.4rem; }
.aw-wordmark{
    display:flex; align-items:baseline; gap:8px;
    padding: 0 0.4rem 0.9rem 0.4rem;
    border-bottom: 1px solid var(--line);
    margin-bottom: 0.9rem;
}
.aw-wordmark .mark{
    width:20px; height:20px; border:1.5px solid var(--amber); border-radius:3px;
    display:inline-flex; align-items:center; justify-content:center;
    color: var(--amber); font-size:12px; font-weight:600; flex:none;
}
.aw-wordmark .name{ font-weight:600; font-size:0.95rem; color: var(--ink); letter-spacing:0.01em; }
.aw-wordmark .tag{ font-size:0.68rem; color: var(--ink-low); text-transform: uppercase; letter-spacing:0.08em; }

section[data-testid="stSidebar"] div[role="radiogroup"]{ gap: 1px; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label{
    border-left: 2px solid transparent;
    padding: 8px 10px 8px 8px;
    border-radius: 0;
    color: var(--ink-mid);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover{
    background: var(--panel-alt);
    color: var(--ink);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked){
    border-left: 2px solid var(--amber);
    background: var(--panel-alt);
    color: var(--ink);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{ font-weight:500; font-size:0.88rem; }
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p{ color: var(--ink-low); }

/* sidebar footer status strip */
.aw-rail-status{
    margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid var(--line);
    display:flex; flex-direction:column; gap:6px;
}
.aw-rail-row{ display:flex; align-items:center; gap:8px; font-size:0.76rem; color: var(--ink-mid); }
.aw-dot{ width:6px; height:6px; border-radius:50%; background: var(--ink-low); flex:none; }
.aw-dot.good{ background: var(--good); }
.aw-dot.bad{ background: var(--bad); }

/* ---- Typography ---- */
h1, h2, h3, h4{ color: var(--ink) !important; font-weight:600 !important; letter-spacing:-0.005em; }
p, span, label, .stMarkdown{ color: var(--ink-mid); }
hr{ border-color: var(--line) !important; margin: 1.1rem 0 !important; }

/* ---- Page header component ---- */
.aw-header{
    display:flex; justify-content:space-between; align-items:flex-end;
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.9rem; margin-bottom: 1.3rem;
}
.aw-header h1{ font-size:1.35rem !important; margin:0 !important; }
.aw-header .sub{ font-size:0.85rem; color: var(--ink-low); margin-top:2px; }
.aw-header .env{
    font-size:0.72rem; color: var(--ink-low); border: 1px solid var(--line);
    padding: 3px 9px; border-radius: var(--radius); white-space:nowrap;
}

/* ---- Section label ---- */
.aw-section{ font-size:0.82rem; font-weight:600; color: var(--ink); margin: 1.6rem 0 0.7rem 0; }

/* ---- Flat panels (replace shadow cards) ---- */
div[data-testid="stVerticalBlockBorderWrapper"]{
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
}
div[data-testid="stForm"]{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 1.3rem 1.4rem 0.3rem 1.4rem;
    box-shadow: none;
}

/* ---- Metrics (stat blocks) ---- */
div[data-testid="stMetric"]{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 14px 16px;
}
div[data-testid="stMetricLabel"]{
    color: var(--ink-low) !important; font-weight:500 !important; font-size:0.72rem !important;
}
div[data-testid="stMetricValue"]{ color: var(--ink) !important; font-weight:600 !important; font-size:1.5rem !important; }
div[data-testid="stMetricDelta"]{ color: var(--ink-mid) !important; }

/* ---- Inputs ---- */
.stTextInput input, .stNumberInput input, textarea,
.stMultiSelect [data-baseweb="select"] > div{
    background: var(--panel-alt) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
}
.stTextInput input:focus, textarea:focus{
    border-color: var(--line-strong) !important;
    box-shadow: 0 0 0 1px var(--line-strong) !important;
}
.stTextInput label p, .stNumberInput label p, .stMultiSelect label p, .stCheckbox label p{
    color: var(--ink-mid) !important; font-weight:500 !important; font-size:0.85rem !important;
}
::placeholder{ color: var(--ink-low) !important; opacity:1; }
.stMultiSelect span[data-baseweb="tag"]{
    background: var(--panel-alt) !important; color: var(--ink) !important;
    border: 1px solid var(--line-strong) !important; border-radius: 4px !important;
}

/* ---- Buttons: flat + hairline; primary uses the amber accent ---- */
.stButton button, .stFormSubmitButton button{
    background: var(--panel-alt) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    transition: border-color 0.12s ease, background 0.12s ease;
}
.stButton button:hover, .stFormSubmitButton button:hover{
    border-color: var(--ink-low) !important;
    background: #202327 !important;
}
.stButton button p, .stFormSubmitButton button p{ color: var(--ink) !important; }

button[kind="primary"], .stFormSubmitButton button[kind="primary"]{
    background: var(--amber) !important;
    border: 1px solid var(--amber) !important;
}
button[kind="primary"] p{ color: var(--amber-ink) !important; font-weight:600 !important; }
button[kind="primary"]:hover{ filter: brightness(1.06); }

/* ---- Code / mono values ---- */
.stCodeBlock{ background:#0a0b0c !important; border:1px solid var(--line) !important; border-radius: var(--radius) !important; }
.stCodeBlock code{ color:#c8cdd3 !important; }

/* ---- Alerts: flat, left rule instead of filled block ---- */
div[data-testid="stAlert"]{
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-left: 3px solid var(--ink-low) !important;
    border-radius: var(--radius) !important;
}
div[data-testid="stAlertContentSuccess"]{ color:#bfe3cd !important; }
div[data-testid="stAlertContentError"]{ color:#f0cccc !important; }
div[data-testid="stAlertContentWarning"]{ color:#ecd8ab !important; }
div[data-testid="stAlertContentInfo"]{ color:#c7d0d8 !important; }

/* status pill used for active/inactive + connection state */
.aw-pill{ display:inline-flex; align-items:center; gap:6px; font-size:0.82rem; color: var(--ink-mid); }
.aw-pill .aw-dot{ width:7px; height:7px; }

/* ---- Row list item (used for resources / channels) ---- */
.aw-row-title{ font-size:0.98rem; font-weight:600; color: var(--ink); margin:0; }
.aw-row-id{ color: var(--ink-low); font-size:0.78rem; }
.aw-field-label{ font-size:0.72rem; color: var(--ink-low); text-transform:none; margin: 0.5rem 0 0.15rem 0; }

/* ---- Responsive: phones ---- */
@media (max-width: 640px){
    .block-container{ padding-left: 0.85rem !important; padding-right: 0.85rem !important; padding-top: 4rem !important; }
    .aw-header{ flex-direction: column; align-items:flex-start; gap:6px; }
    .aw-header h1{ font-size: 1.15rem !important; }
    div[data-testid="stForm"]{ padding: 1rem; }
    div[data-testid="stMetric"]{ padding: 10px 12px; }
    .stButton button, .stFormSubmitButton button{ width: 100%; }
}
</style>
""",
    unsafe_allow_html=True,
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
    st.error("`SUPABASE_URL` and `SUPABASE_KEY` are required in `.env` or Streamlit secrets.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def get_db_setting(key: str, default: str = "") -> str:
    """Retrieve a setting from the Supabase bot_settings table."""
    try:
        res = (
            supabase.table("bot_settings")
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        if res.data and len(res.data) > 0:
            val = res.data[0].get("value")
            if val is not None and str(val).strip():
                return str(val).strip()
    except Exception:
        pass
    return default


def set_db_setting(key: str, value: str) -> bool:
    """Persist a setting to the Supabase bot_settings table."""
    try:
        res = (
            supabase.table("bot_settings")
            .upsert({"key": key, "value": value})
            .execute()
        )
        return bool(res.data)
    except Exception:
        return False


def hash_password(password: str, salt: str = "") -> str:
    """Hash a password using SHA-256 with a random salt."""
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{pwd_hash}"


def verify_password(stored_hash_val: str, provided_password: str) -> bool:
    """Verify a plain-text password against a stored salt:hash string."""
    if not stored_hash_val or ":" not in stored_hash_val:
        return False
    salt, actual_hash = stored_hash_val.split(":", 1)
    test_hash = hashlib.sha256((salt + provided_password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(test_hash, actual_hash)


def get_admin_credentials() -> tuple[str, str]:
    """
    Retrieve admin username and password hash from Supabase bot_settings.
    If not found, initializes default credentials from secrets/env or 'admin' / 'admin123'.
    """
    db_user = get_db_setting("admin_username")
    db_pwd_hash = get_db_setting("admin_password_hash")

    if db_user and db_pwd_hash:
        return db_user, db_pwd_hash

    fallback_user = "admin"
    fallback_pwd = "admin123"
    try:
        if "ADMIN_USERNAME" in st.secrets and str(st.secrets["ADMIN_USERNAME"]).strip():
            fallback_user = str(st.secrets["ADMIN_USERNAME"]).strip()
        if "ADMIN_PASSWORD" in st.secrets and str(st.secrets["ADMIN_PASSWORD"]).strip():
            fallback_pwd = str(st.secrets["ADMIN_PASSWORD"]).strip()
    except Exception:
        pass

    fallback_user = os.getenv("ADMIN_USERNAME", fallback_user).strip()
    fallback_pwd = os.getenv("ADMIN_PASSWORD", fallback_pwd).strip()

    pwd_hash = hash_password(fallback_pwd)
    set_db_setting("admin_username", fallback_user)
    set_db_setting("admin_password_hash", pwd_hash)
    return fallback_user, pwd_hash


def update_admin_credentials(new_username: str, new_password: str) -> bool:
    """Update admin username and hashed password in Supabase bot_settings."""
    new_username = new_username.strip()
    new_password = new_password.strip()
    if not new_username or not new_password:
        return False
    pwd_hash = hash_password(new_password)
    ok_user = set_db_setting("admin_username", new_username)
    ok_pwd = set_db_setting("admin_password_hash", pwd_hash)
    return ok_user and ok_pwd


def render_login_page() -> None:
    """Render a clean, secure admin login interface."""
    render_page_header("System Authentication", "Sign in to access the administration console.", env_label="Secured")

    _, col_mid, _ = st.columns([1, 1.3, 1])
    with col_mid:
        with st.form("admin_login_form"):
            st.markdown(
                """
                <div style="margin-bottom: 1.2rem;">
                    <div style="font-weight: 600; font-size: 1.05rem; color: var(--ink);">Admin Login</div>
                    <div style="font-size: 0.8rem; color: var(--ink-low); margin-top: 2px;">Enter authorized credentials to continue</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            input_user = st.text_input("Username", placeholder="admin")
            input_pwd = st.text_input("Password", type="password", placeholder="••••••••")
            submit_login = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if submit_login:
            stored_user, stored_hash = get_admin_credentials()
            input_user = input_user.strip()
            if input_user == stored_user and verify_password(stored_hash, input_pwd):
                st.session_state["authenticated"] = True
                st.session_state["admin_user"] = stored_user
                st.rerun()
            else:
                st.error("Authentication failed: Invalid username or password.")


def get_bot_token_with_source() -> tuple[str, str]:
    """
    Retrieve bot token and its source:
    1. Supabase database (bot_settings table)
    2. Streamlit secrets
    3. Environment variable / .env
    """
    db_token = get_db_setting("telegram_bot_token")
    if db_token:
        return db_token, "Supabase Database"

    try:
        if "TELEGRAM_BOT_TOKEN" in st.secrets and str(st.secrets["TELEGRAM_BOT_TOKEN"]).strip():
            return str(st.secrets["TELEGRAM_BOT_TOKEN"]).strip(), "Streamlit Secrets"
        if "BOT_TOKEN" in st.secrets and str(st.secrets["BOT_TOKEN"]).strip():
            return str(st.secrets["BOT_TOKEN"]).strip(), "Streamlit Secrets"
    except Exception:
        pass

    env_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if env_token and env_token.strip():
        return env_token.strip(), "Environment (.env)"

    if ENV_PATH.exists():
        try:
            for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    val = line.split("=", 1)[1].strip(" '\"")
                    if val:
                        return val, "Local .env file"
                if line.startswith("BOT_TOKEN="):
                    val = line.split("=", 1)[1].strip(" '\"")
                    if val:
                        return val, "Local .env file"
        except Exception:
            pass

    return "", "None"


def get_bot_token() -> str:
    """Retrieve current Telegram bot token."""
    token, _ = get_bot_token_with_source()
    return token


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
    """Safely update or add TELEGRAM_BOT_TOKEN in .env file if available."""
    new_token = new_token.strip()
    lines = []
    found = False

    if ENV_PATH.exists():
        try:
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
        except Exception:
            pass

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
# Presentation helpers (visual only — no state or business logic)
# ---------------------------------------------------------------------------
def render_page_header(title: str, subtitle: str, env_label: str = "Production") -> None:
    st.markdown(
        f"""
        <div class="aw-header">
            <div>
                <h1>{title}</h1>
                <div class="sub">{subtitle}</div>
            </div>
            <div class="env">{env_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_label(text: str) -> None:
    st.markdown(f'<div class="aw-section">{text}</div>', unsafe_allow_html=True)


def status_pill_html(is_on: bool, on_label: str, off_label: str) -> str:
    dot_class = "good" if is_on else "bad"
    label = on_label if is_on else off_label
    return f'<span class="aw-pill"><span class="aw-dot {dot_class}"></span>{label}</span>'


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Authentication Gate
# ---------------------------------------------------------------------------
if not st.session_state.get("authenticated", False):
    render_login_page()
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div class="aw-wordmark">
        <span class="mark">A</span>
        <div>
            <div class="name">Anime World</div>
            <div class="tag">Admin Console</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Anime Resources", "Telegram Channels", "Bot Settings", "Admin Security"],
    index=0,
    label_visibility="collapsed",
)

current_bot_token = get_bot_token()
bot_username_env = os.getenv("BOT_USERNAME", "").strip().lstrip("@")

_bot_configured = bool(current_bot_token)
st.sidebar.markdown(
    f"""
    <div class="aw-rail-status">
        <div class="aw-rail-row"><span class="aw-dot good"></span>Database connected</div>
        <div class="aw-rail-row"><span class="aw-dot {'good' if _bot_configured else 'bad'}"></span>
            Bot token {'configured' if _bot_configured else 'missing'}</div>
        <div class="aw-rail-row"><span class="aw-dot good"></span>User: {st.session_state.get('admin_user', 'admin')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.sidebar.button("Sign out", use_container_width=True):
    st.session_state["authenticated"] = False
    st.rerun()


# ---------------------------------------------------------------------------
# Page 1: Dashboard
# ---------------------------------------------------------------------------
if selected_page == "Dashboard":
    render_page_header("Dashboard", "System overview and live statistics.")

    try:
        total_resources = count_rows("resources")
        total_channels = count_rows("telegram_channels")
        total_users = count_rows("users")
    except Exception as exc:
        st.error(f"Failed to fetch database counts: {exc}")
        total_resources = total_channels = total_users = 0

    bot_online = False
    bot_display = "Not configured"
    bot_sub = "Configure in Bot Settings"

    if current_bot_token:
        is_valid, b_info = check_telegram_bot(current_bot_token)
        if is_valid and isinstance(b_info, dict):
            bot_online = True
            bot_display = "Online"
            bot_sub = f"@{b_info.get('username', 'bot')}"
        else:
            bot_display = "Error"
            bot_sub = "Invalid token"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total resources", total_resources)
    col2.metric("Telegram channels", total_channels)
    col3.metric("Registered users", total_users)
    col4.metric("Bot status", bot_display, bot_sub)




# ---------------------------------------------------------------------------
# Page 2: Anime Resources
# ---------------------------------------------------------------------------
elif selected_page == "Anime Resources":
    render_page_header("Anime Resources", "Create resources and generate Telegram deep links. Files stay on Google Drive.")

    # Determine bot username for link generation
    active_bot_username = get_db_setting("bot_username") or bot_username_env
    if not active_bot_username and current_bot_token:
        ok, info = check_telegram_bot(current_bot_token)
        if ok and isinstance(info, dict):
            active_bot_username = info.get("username", "")
            if active_bot_username:
                set_db_setting("bot_username", active_bot_username)

    if not active_bot_username:
        st.warning("Bot username not detected. Configure Bot Settings or set `BOT_USERNAME` in `.env`.")

    try:
        channel_rows = supabase.table("telegram_channels").select("id,name").eq("is_active", True).order("name").execute().data or []
    except Exception as exc:
        st.error(f"Failed to load channels: {exc}")
        channel_rows = []

    render_section_label("Add a resource")
    with st.form("add_resource_form"):
        name = st.text_input("Anime / resource name", placeholder="Solo Leveling S01 — Complete Series")
        drive_url = st.text_input("Google Drive link", placeholder="https://drive.google.com/...")
        options = {f"{row['name']} (ID {row['id']})": row['id'] for row in channel_rows}
        selected = st.multiselect("Required channels", list(options), help="Users must join all selected channels to unlock the download.")
        active = st.checkbox("Resource is active", True)
        submitted = st.form_submit_button("Create resource", use_container_width=True, type="primary")

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
                    st.success("Resource created successfully.")
                    if active_bot_username:
                        st.code(f"https://t.me/{active_bot_username}?start=resource_{rid}")
                    st.rerun()
            except Exception as exc:
                st.error(f"Failed to create resource: {exc}")

    render_section_label("Existing resources")
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
            with c1:
                st.markdown(f'<p class="aw-row-title">{resource.get("name", "Unnamed resource")}</p>', unsafe_allow_html=True)
                st.markdown(f'<span class="aw-row-id">ID {rid}</span>', unsafe_allow_html=True)
            with c2:
                st.markdown(status_pill_html(is_res_active, "Active", "Inactive"), unsafe_allow_html=True)

            st.markdown('<div class="aw-field-label">Google Drive link</div>', unsafe_allow_html=True)
            st.code(resource.get("drive_url") or "Not configured")
            st.markdown('<div class="aw-field-label">Telegram deep link</div>', unsafe_allow_html=True)
            st.code(bot_link or "Bot username required to generate link")

            try:
                required = supabase.table("resource_required_channels").select("channel_id, telegram_channels(name)").eq("resource_id", rid).execute().data or []
                names = []
                for row in required:
                    channel = row.get("telegram_channels")
                    if isinstance(channel, list):
                        channel = channel[0] if channel else None
                    if channel:
                        names.append(channel.get("name", "Unnamed channel"))
                st.markdown('<div class="aw-field-label">Required channels</div>', unsafe_allow_html=True)
                st.write(", ".join(names) if names else "None")
            except Exception as exc:
                st.warning(f"Could not load required channels: {exc}")

            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("Disable" if is_res_active else "Enable", key=f"toggle_res_{rid}", use_container_width=True):
                supabase.table("resources").update({"is_active": not is_res_active}).eq("id", rid).execute()
                st.rerun()
            if btn_col2.button("Delete", key=f"del_res_{rid}", use_container_width=True):
                try:
                    supabase.table("resource_required_channels").delete().eq("resource_id", rid).execute()
                except Exception:
                    pass
                supabase.table("resources").delete().eq("id", rid).execute()
                st.rerun()


# ---------------------------------------------------------------------------
# Page 3: Telegram Channels
# ---------------------------------------------------------------------------
elif selected_page == "Telegram Channels":
    render_page_header("Telegram Channels", "Manage channels users must join before unlocking resource links.")

    st.info(
        "Add your Telegram bot as an **Administrator** in each channel below, "
        "and confirm it has the **Invite Users via Link** permission."
    )

    render_section_label("Add a channel")
    with st.form("add_channel_form"):
        ch_name = st.text_input("Channel name", placeholder="Anime World Updates")
        chat_id_text = st.text_input("Telegram chat ID", placeholder="-1001234567890")
        ch_username = st.text_input("Public username (optional)", placeholder="@examplechannel")
        manual_link = st.text_input("Existing invite link (optional)", placeholder="Leave empty to auto-generate a join-request link")
        ch_submitted = st.form_submit_button("Add channel", use_container_width=True, type="primary")

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
                            st.error(msg)
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
                                    st.success(f"Channel '{ch_name}' added successfully. Bot admin status verified.")
                                    st.rerun()
                                st.error("Channel was not created in database.")
                except Exception as exc:
                    st.error(f"Failed to add channel: {exc}")

    render_section_label("Existing channels")
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
            with c1:
                st.markdown(f'<p class="aw-row-title">{ch.get("name", "Unnamed channel")}</p>', unsafe_allow_html=True)
                st.markdown(f'<span class="aw-row-id">Chat ID {chat_id_val}</span>', unsafe_allow_html=True)
            with c2:
                st.markdown(status_pill_html(ch_active, "Active", "Inactive"), unsafe_allow_html=True)

            st.markdown('<div class="aw-field-label">Username</div>', unsafe_allow_html=True)
            st.write(ch.get("username") or "—")
            if ch.get("invite_link"):
                st.markdown('<div class="aw-field-label">Invite / join-request link</div>', unsafe_allow_html=True)
                st.code(ch["invite_link"])

            test_col, b_col1, b_col2 = st.columns([2, 1, 1])
            if test_col.button("Check bot permissions", key=f"test_ch_{cid}", use_container_width=True):
                if chat_id_val:
                    with st.spinner("Testing bot access to channel..."):
                        t_ok, t_msg, t_det = check_bot_channel_permission(chat_id_val)
                    if t_ok:
                        st.success(t_msg)
                    else:
                        st.error(t_msg)
            if b_col1.button("Disable" if ch_active else "Enable", key=f"toggle_ch_{cid}", use_container_width=True):
                supabase.table("telegram_channels").update({"is_active": not ch_active}).eq("id", cid).execute()
                st.rerun()
            if b_col2.button("Delete", key=f"del_ch_{cid}", use_container_width=True):
                try:
                    supabase.table("resource_required_channels").delete().eq("channel_id", cid).execute()
                except Exception:
                    pass
                supabase.table("telegram_channels").delete().eq("id", cid).execute()
                st.rerun()


# ---------------------------------------------------------------------------
# Page 4: Bot Settings
# ---------------------------------------------------------------------------
elif selected_page == "Bot Settings":
    render_page_header("Bot Settings", "Manage and sync your Telegram Bot API token across Streamlit and Render.")

    current_token, token_source = get_bot_token_with_source()

    render_section_label("Current status")
    if current_token:
        is_valid, bot_info = check_telegram_bot(current_token)
        if is_valid and isinstance(bot_info, dict):
            col1, col2, col3 = st.columns(3)
            col1.metric("Connection", "Connected", f"via {token_source}")
            col2.metric("Bot username", f"@{bot_info.get('username', 'N/A')}")
            col3.metric("Bot ID", str(bot_info.get("id", "N/A")))

            st.success(
                f"Active bot: **{bot_info.get('first_name', 'Bot')}** "
                f"([@{bot_info.get('username')}](https://t.me/{bot_info.get('username')})) — "
                f"Token source: `{token_source}`"
            )
        else:
            st.error(f"Current token is invalid or unreachable ({token_source}): {bot_info}")
    else:
        st.warning("No Telegram Bot API token is currently configured.")

    render_section_label("Update bot API key")
    st.write(
        "Enter a new Telegram Bot API token generated from "
        "[@BotFather](https://t.me/BotFather) on Telegram. "
        "Saving here persists it directly into Supabase, so your bot worker automatically connects."
    )

    with st.form("update_bot_token_form"):
        new_token_input = st.text_input(
            "New bot API token",
            type="password",
            placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            help="Paste the bot token from @BotFather here.",
        )
        token_submitted = st.form_submit_button("Test & save token to Supabase", use_container_width=True, type="primary")

    if token_submitted:
        if not new_token_input.strip():
            st.error("Please enter a valid bot token.")
        else:
            token_to_test = new_token_input.strip()
            with st.spinner("Testing token with Telegram API..."):
                valid, info = check_telegram_bot(token_to_test)

            if valid and isinstance(info, dict):
                saved_to_db = set_db_setting("telegram_bot_token", token_to_test)
                if info.get("username"):
                    set_db_setting("bot_username", info["username"])

                try:
                    update_env_file(token_to_test)
                except Exception:
                    pass

                if saved_to_db:
                    st.success(
                        f"Token successfully validated and saved to Supabase.\n\n"
                        f"- Bot name: {info.get('first_name')}\n"
                        f"- Username: @{info.get('username')}\n"
                        f"- Bot ID: {info.get('id')}\n\n"
                        f"Your bot worker will automatically fetch and use this token."
                    )
                else:
                    st.warning("Token is valid, but could not be saved to Supabase bot_settings table.")
                st.rerun()
            else:
                st.error(f"Telegram API rejected this token: {info}")


# ---------------------------------------------------------------------------
# Page 5: Admin Security
# ---------------------------------------------------------------------------
elif selected_page == "Admin Security":
    render_page_header("Admin Security", "Manage administrator authentication and credentials.")

    current_admin_user, _ = get_admin_credentials()

    render_section_label("Account overview")
    col1, col2 = st.columns(2)
    col1.metric("Current admin", current_admin_user)
    col2.metric("Authentication storage", "Supabase Database")

    render_section_label("Change credentials")
    st.write("Update your admin username and password. Changes are saved directly to Supabase and persist across reboots.")

    with st.form("change_admin_credentials_form"):
        curr_pwd_input = st.text_input("Current password", type="password", placeholder="Enter current password")
        new_user_input = st.text_input("New username", value=current_admin_user)
        new_pwd_input = st.text_input("New password", type="password", placeholder="Enter new password")
        confirm_pwd_input = st.text_input("Confirm new password", type="password", placeholder="Confirm new password")
        save_cred_submitted = st.form_submit_button("Update credentials", use_container_width=True, type="primary")

    if save_cred_submitted:
        _, stored_hash = get_admin_credentials()
        if not curr_pwd_input.strip():
            st.error("Please enter your current password.")
        elif not verify_password(stored_hash, curr_pwd_input.strip()):
            st.error("Current password is incorrect.")
        elif not new_user_input.strip():
            st.error("Username cannot be empty.")
        elif not new_pwd_input.strip():
            st.error("New password cannot be empty.")
        elif len(new_pwd_input.strip()) < 4:
            st.error("New password must be at least 4 characters.")
        elif new_pwd_input != confirm_pwd_input:
            st.error("New passwords do not match.")
        else:
            ok = update_admin_credentials(new_user_input.strip(), new_pwd_input.strip())
            if ok:
                st.session_state["admin_user"] = new_user_input.strip()
                st.success("Admin credentials successfully updated and stored in Supabase.")
                st.rerun()
            else:
                st.error("Failed to update credentials in Supabase.")