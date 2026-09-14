from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def required_channels_keyboard(missing_channels: list, total_channels: int, resource_id: int) -> InlineKeyboardMarkup:
    """
    Build keyboard dynamically:
    - Adds buttons only for unjoined / missing channels.
    - As channels are joined, their buttons are removed.
    - Shows progress count on the verify/check button.
    """
    builder = InlineKeyboardBuilder()

    for idx, channel in enumerate(missing_channels, start=1):
        invite_link = channel.get("invite_link")
        name = channel.get("name", f"Channel {idx}")
        if invite_link:
            builder.button(
                text=f"📢 Join {name}",
                url=invite_link,
            )

    if not missing_channels:
        builder.button(
            text="✨ Verify & Unlock Download",
            callback_data=f"verify:{resource_id}",
        )
    else:
        completed = max(0, total_channels - len(missing_channels))
        builder.button(
            text=f"🔄 Check Progress ({completed}/{total_channels})",
            callback_data=f"verify:{resource_id}",
        )

    builder.adjust(1)
    return builder.as_markup()


def download_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Download Anime Now", url=url)
    return builder.as_markup()
