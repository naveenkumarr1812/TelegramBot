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


def get_channel_by_chat_id(chat_id: int) -> Optional[dict]:
    """Fetch a channel record from telegram_channels by its chat_id."""
    try:
        res = (
            supabase.table("telegram_channels")
            .select("*")
            .eq("chat_id", chat_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.error("Could not fetch channel by chat_id %s: %s", chat_id, exc)
        return None


def record_channel_join_request(user_db_id: int, channel_db_id: int) -> bool:
    """
    Record a user's join request in channel_join_requests without approving it.
    Does not duplicate records if already present.
    """
    try:
        existing = (
            supabase.table("channel_join_requests")
            .select("id")
            .eq("user_id", user_db_id)
            .eq("channel_id", channel_db_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return True

        supabase.table("channel_join_requests").insert({
            "user_id": user_db_id,
            "channel_id": channel_db_id,
            "status": "requested",
        }).execute()
        logger.info("Recorded join request in Supabase for user_id=%s, channel_id=%s", user_db_id, channel_db_id)
        return True
    except Exception as exc:
        logger.error("Failed to record channel join request: %s", exc)
        return False


def get_user_requested_channel_ids(telegram_user_id: int) -> set[int]:
    """
    Retrieve the set of channel IDs (primary keys) that the user has already
    requested to join or joined in Supabase.
    """
    try:
        user_res = (
            supabase.table("users")
            .select("id")
            .eq("telegram_id", telegram_user_id)
            .limit(1)
            .execute()
        )
        if not user_res.data:
            return set()

        user_db_id = user_res.data[0]["id"]
        res = (
            supabase.table("channel_join_requests")
            .select("channel_id")
            .eq("user_id", user_db_id)
            .execute()
        )
        if res.data:
            return {row["channel_id"] for row in res.data if "channel_id" in row and row["channel_id"] is not None}
    except Exception as exc:
        logger.debug("Error checking requested channels for user %s: %s", telegram_user_id, exc)
    return set()


