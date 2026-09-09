import logging

from aiogram import Bot


logger = logging.getLogger(__name__)


# Telegram membership statuses that are considered valid
VALID_STATUSES = {
    "member",
    "administrator",
    "creator",
}


async def verify_user_channels(
    bot: Bot,
    user_id: int,
    channels: list,
) -> list:
    """
    Check whether a Telegram user has joined
    all required channels.

    Returns:
        List of channels that the user has NOT joined.
    """

    missing_channels = []

    for channel in channels:

        channel_name = channel.get(
            "name",
            "Unknown Channel",
        )

        chat_id = channel.get(
            "chat_id"
        )

        logger.info(
            "Checking user %s in channel '%s' | chat_id=%s",
            user_id,
            channel_name,
            chat_id,
        )

        # ----------------------------------------------------
        # Validate chat ID
        # ----------------------------------------------------

        if chat_id is None:

            logger.error(
                "Channel '%s' has no chat_id.",
                channel_name,
            )

            missing_channels.append(
                channel
            )

            continue

        # ----------------------------------------------------
        # Telegram membership check
        # ----------------------------------------------------

        try:

            member = await bot.get_chat_member(
                chat_id=chat_id,
                user_id=user_id,
            )

            logger.info(
                "Telegram response | channel='%s' | "
                "user=%s | status=%s",
                channel_name,
                user_id,
                member.status,
            )

            # ------------------------------------------------
            # Check membership status
            # ------------------------------------------------

            if member.status not in VALID_STATUSES:

                logger.info(
                    "User %s has NOT joined '%s'. "
                    "Status=%s",
                    user_id,
                    channel_name,
                    member.status,
                )

                missing_channels.append(
                    channel
                )

            else:

                logger.info(
                    "User %s IS a member of '%s'.",
                    user_id,
                    channel_name,
                )

        except Exception as error:

            logger.exception(
                "Telegram membership check FAILED | "
                "channel='%s' | chat_id=%s | user=%s",
                channel_name,
                chat_id,
                user_id,
            )

            # Treat failed verification as missing
            missing_channels.append(
                channel
            )

    return missing_channels