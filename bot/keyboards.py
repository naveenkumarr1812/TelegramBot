from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def required_channels_keyboard(channels: list, resource_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for channel in channels:
        invite_link = channel.get("invite_link")
        if invite_link:
            builder.button(
                text=f"📢 {channel.get('name', 'Join Channel')}",
                url=invite_link,
            )
    builder.button(text="🔄 Verify Again", callback_data=f"verify:{resource_id}")
    builder.adjust(1)
    return builder.as_markup()


def download_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Download", url=url)
    return builder.as_markup()
