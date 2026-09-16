import logging
from typing import Optional

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_or_create_user(
    telegram_user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
):
    result = (
        supabase.table("users")
        .select("*")
        .eq("telegram_id", telegram_user_id)
        .limit(1)
        .execute()
    )
    if result.data:
        user = result.data[0]
        update = {
            "username": username,
            "first_name": first_name,
        }
        # Only send last_name when the Telegram user actually has one.
        if last_name is not None:
            update["last_name"] = last_name
        try:
            updated = (
                supabase.table("users")
                .update(update)
                .eq("id", user["id"])
                .execute()
            )
            if updated.data:
                return updated.data[0]
        except Exception as exc:
            # Some older schemas may not contain optional profile columns.
            logger.warning("Could not update optional user fields: %s", exc)
        return user

    data = {
        "telegram_id": telegram_user_id,
        "username": username,
        "first_name": first_name,
    }
    if last_name is not None:
        data["last_name"] = last_name

    created = supabase.table("users").insert(data).execute()
    if not created.data:
        raise RuntimeError("Supabase did not return the created user.")
    return created.data[0]


def get_resource(resource_id: int):
    result = (
        supabase.table("resources")
        .select("*")
        .eq("id", resource_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_required_channels(resource_id: int):
    result = (
        supabase.table("resource_required_channels")
        .select(
            "channel_id, telegram_channels(id, name, chat_id, username, invite_link, is_active)"
        )
        .eq("resource_id", resource_id)
        .execute()
    )
    channels = []
    for row in result.data or []:
        channel = row.get("telegram_channels")
        if isinstance(channel, list):
            channel = channel[0] if channel else None
        if channel and channel.get("is_active", True):
            channels.append(channel)
    return channels


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve a configuration value from the bot_settings table."""
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
    except Exception as exc:
        logger.debug("Could not read setting '%s' from bot_settings: %s", key, exc)
    return default


def set_setting(key: str, value: str) -> bool:
    """Upsert a configuration key/value into the bot_settings table."""
    try:
        res = (
            supabase.table("bot_settings")
            .upsert({"key": key, "value": value})
            .execute()
        )
        return bool(res.data)
    except Exception as exc:
        logger.error("Failed to update bot_setting '%s': %s", key, exc)
        return False


def get_all_settings() -> dict[str, str]:
    """Retrieve all configuration key/value pairs from bot_settings."""
    try:
        res = supabase.table("bot_settings").select("key, value").execute()
        if res.data:
            return {
                row["key"]: row["value"]
                for row in res.data
                if "key" in row and row["value"] is not None
            }
    except Exception as exc:
        logger.debug("Could not retrieve all bot_settings: %s", exc)
    return {}

