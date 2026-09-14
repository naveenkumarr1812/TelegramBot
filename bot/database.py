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
