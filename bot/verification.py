import logging
from aiogram import Bot

from database import get_user_requested_channel_ids, record_channel_join_request, supabase

logger = logging.getLogger(__name__)

# Valid member statuses in Telegram
VALID_STATUSES = {"member", "administrator", "creator", "restricted"}


async def verify_user_channels(bot: Bot, user_id: int, channels: list) -> list:
    missing = []
    # 1. Fetch channel IDs that the user has already requested or joined in Supabase
    requested_channel_ids = get_user_requested_channel_ids(user_id)

    for channel in channels:
        ch_id = channel.get("id")
        ch_name = channel.get("name", "Unknown Channel")
        chat_id = channel.get("chat_id")

        # If user has already sent a join request (recorded in Supabase), requirement is satisfied!
        if ch_id and ch_id in requested_channel_ids:
            logger.info("Verification passed: user %s has recorded join request for '%s' (channel_id=%s)", user_id, ch_name, ch_id)
            continue

        if chat_id is None:
            logger.error("Channel '%s' has no chat_id configured.", ch_name)
            missing.append(channel)
            continue

        # 2. Check if user is already an accepted member in the channel on Telegram
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            status = getattr(member, "status", None)
            is_member = getattr(member, "is_member", True) if status == "restricted" else True
            logger.info(
                "Membership check | user=%s channel='%s' (chat_id=%s) | status=%s is_member=%s",
                user_id,
                ch_name,
                chat_id,
                status,
                is_member,
            )
            if status in VALID_STATUSES and (status != "restricted" or is_member):
                # User is a member, record in Supabase so future checks are instant without Telegram API
                try:
                    u_res = supabase.table("users").select("id").eq("telegram_id", user_id).limit(1).execute()
                    if u_res.data and ch_id:
                        record_channel_join_request(u_res.data[0]["id"], ch_id)
                except Exception:
                    pass
                continue

            missing.append(channel)
        except Exception as exc:
            logger.warning(
                "Membership check failed | user=%s channel='%s' (chat_id=%s): %s. "
                "(Ensure the bot is added as an Administrator in this channel)",
                user_id,
                ch_name,
                chat_id,
                exc,
            )
            missing.append(channel)

    return missing

