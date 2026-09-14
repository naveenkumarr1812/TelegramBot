import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

# Valid member statuses in Telegram
VALID_STATUSES = {"member", "administrator", "creator", "restricted"}


async def verify_user_channels(bot: Bot, user_id: int, channels: list) -> list:
    missing = []
    for channel in channels:
        name = channel.get("name", "Unknown Channel")
        chat_id = channel.get("chat_id")
        if chat_id is None:
            logger.error("Channel '%s' has no chat_id configured.", name)
            missing.append(channel)
            continue
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            status = getattr(member, "status", None)
            is_member = getattr(member, "is_member", True) if status == "restricted" else True
            logger.info(
                "Membership check | user=%s channel='%s' (chat_id=%s) | status=%s is_member=%s",
                user_id,
                name,
                chat_id,
                status,
                is_member,
            )
            if status not in VALID_STATUSES or (status == "restricted" and not is_member):
                missing.append(channel)
        except Exception as exc:
            logger.warning(
                "Membership check failed | user=%s channel='%s' (chat_id=%s): %s. "
                "(Ensure the bot is added as an Administrator in this channel)",
                user_id,
                name,
                chat_id,
                exc,
            )
            missing.append(channel)
    return missing
