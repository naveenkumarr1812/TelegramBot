import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import CallbackQuery, Message

from config import TELEGRAM_BOT_TOKEN
from database import get_or_create_user
from keyboards import download_keyboard, required_channels_keyboard
from services import get_required_channels, get_resource, parse_resource_parameter
from verification import verify_user_channels

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("animeworld.bot")

bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()


async def send_resource_result(target: Message, user_id: int, resource_id: int) -> None:
    resource = get_resource(resource_id)
    if not resource:
        await target.answer("❌ This resource does not exist or is inactive.")
        return

    channels = get_required_channels(resource_id)
    missing = await verify_user_channels(bot, user_id, channels)
    name = resource.get("name", "Anime")
    drive_url = resource.get("drive_url")

    if missing:
        await target.answer(
            f"🔐 <b>Verification Required</b>\n\n"
            f"🎬 <b>{name}</b>\n\n"
            "Join every required channel below, then press "
            "<b>Verify Again</b>.",
            reply_markup=required_channels_keyboard(missing, resource_id),
        )
        return

    if not drive_url:
        await target.answer("⚠️ Verification passed, but the download link is unavailable.")
        return

    await target.answer(
        f"🎉 <b>Verification Successful!</b>\n\n"
        f"🎬 <b>{name}</b>\n\n"
        "Your download is ready:",
        reply_markup=download_keyboard(drive_url),
    )


@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    user = message.from_user
    if not user:
        return

    try:
        get_or_create_user(
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    except Exception:
        logger.exception("Failed to save user %s", user.id)
        await message.answer("⚠️ Could not save your account. Please try again.")
        return

    resource_id = parse_resource_parameter(command.args)
    if resource_id is None:
        await message.answer(
            "👋 <b>Welcome to Anime World!</b>\n\n"
            "Open a download button from the main channel to continue."
        )
        return

    try:
        await send_resource_result(message, user.id, resource_id)
    except Exception:
        logger.exception("Resource flow failed | user=%s resource=%s", user.id, resource_id)
        await message.answer("⚠️ Something went wrong. Please try again later.")


@dp.callback_query(F.data.startswith("verify:"))
async def verify_callback(callback: CallbackQuery):
    await callback.answer("🔍 Checking membership...")
    try:
        resource_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError, AttributeError):
        await callback.answer("❌ Invalid resource.", show_alert=True)
        return

    resource = get_resource(resource_id)
    if not resource:
        await callback.message.edit_text("❌ This resource does not exist or is inactive.")
        return

    channels = get_required_channels(resource_id)
    missing = await verify_user_channels(bot, callback.from_user.id, channels)
    name = resource.get("name", "Anime")
    drive_url = resource.get("drive_url")

    if missing:
        await callback.message.edit_text(
            f"❌ <b>Verification Incomplete</b>\n\n"
            f"🎬 <b>{name}</b>\n\n"
            "You still need to join the channel(s) below.",
            reply_markup=required_channels_keyboard(missing, resource_id),
        )
        return

    if not drive_url:
        await callback.message.edit_text("⚠️ Verification passed, but the download link is unavailable.")
        return

    await callback.message.edit_text(
        f"🎉 <b>Verification Successful!</b>\n\n"
        f"🎬 <b>{name}</b>\n\n"
        "Your download is ready.",
        reply_markup=download_keyboard(drive_url),
    )


async def main():
    me = await bot.get_me()
    logger.info("Starting @%s (id=%s)", me.username, me.id)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
