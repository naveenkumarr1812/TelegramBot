import logging
from aiogram import Bot

logger = logging.getLogger(__name__)
VALID_STATUSES = {"member", "administrator", "creator"}


async def verify_user_channels(bot: Bot, user_id: int, channels: list) -> list:
    missing = []
    for channel in channels:
        name = channel.get("name", "Unknown Channel")
        chat_id = channel.get("chat_id")
        if chat_id is None:
            missing.append(channel)
            continue
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            status = getattr(member, "status", None)
            logger.info("Membership | user=%s channel=%s status=%s", user_id, name, status)
            if status not in VALID_STATUSES:
                missing.append(channel)
        except Exception:
            logger.exception("Membership check failed | user=%s channel=%s", user_id, name)
            missing.append(channel)
    return missing
