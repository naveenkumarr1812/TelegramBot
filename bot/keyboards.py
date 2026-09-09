from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def required_channels_keyboard(
    channels: list,
    resource_id: int,
) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard containing:
    - A button for each required Telegram channel
    - A Verify Again button

    Args:
        channels: List of channel dictionaries.
        resource_id: ID of the requested resource.

    Returns:
        InlineKeyboardMarkup
    """

    builder = InlineKeyboardBuilder()

    # --------------------------------------
    # Channel buttons
    # --------------------------------------

    for channel in channels:

        invite_link = channel.get("invite_link")

        if not invite_link:
            continue

        channel_name = channel.get(
            "name",
            "Join Channel"
        )

        builder.button(
            text=f"📢 {channel_name}",
            url=invite_link,
        )

    # --------------------------------------
    # Verify button
    # --------------------------------------

    builder.button(
        text="🔄 Verify Again",
        callback_data=f"verify:{resource_id}",
    )

    # One button per row
    builder.adjust(1)

    return builder.as_markup()