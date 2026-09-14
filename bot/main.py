import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, ChatJoinRequest, Message

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


def format_progress_message(name: str, total_count: int, missing_count: int) -> str:
    """Format a clean visual progress message for channel requirements."""
    completed = max(0, total_count - missing_count)
    pct = int((completed / total_count) * 100) if total_count > 0 else 100
    bar = "🟩" * completed + "⬜" * missing_count

    if missing_count == 0:
        return (
            f"🎉 <b>All Channels Joined!</b>\n\n"
            f"🎬 <b>{name}</b>\n\n"
            f"📊 <b>Progress</b>: {completed}/{total_count} (100%)\n"
            f"<code>{bar}</code>\n\n"
            f"Click the button below to unlock your download link:"
        )

    return (
        f"🔐 <b>Verification Required</b>\n\n"
        f"🎬 <b>{name}</b>\n\n"
        f"📊 <b>Progress</b>: {completed}/{total_count} Channels Joined ({pct}%)\n"
        f"<code>{bar}</code>\n\n"
        f"👉 Click the channel button(s) below to join/send request.\n"
        f"Once done, click <b>Check Progress</b> to proceed."
    )


async def send_resource_result(target: Message, user_id: int, resource_id: int) -> None:
    resource = get_resource(resource_id)
    if not resource:
        await target.answer("❌ This resource does not exist or is inactive.")
        return

    channels = get_required_channels(resource_id)
    total_count = len(channels)
    missing = await verify_user_channels(bot, user_id, channels)
    name = resource.get("name", "Anime")
    drive_url = resource.get("drive_url")

    if missing:
        msg_text = format_progress_message(name, total_count, len(missing))
        await target.answer(
            msg_text,
            reply_markup=required_channels_keyboard(missing, total_count, resource_id),
        )
        return

    if not drive_url:
        await target.answer("⚠️ Verification passed, but the download link is unavailable.")
        return

    await target.answer(
        f"🎉 <b>Verification Successful!</b>\n\n"
        f"🎬 <b>{name}</b>\n\n"
        f"✅ All {total_count} required channel(s) verified!\n\n"
        "Your download link is ready below:",
        reply_markup=download_keyboard(drive_url),
    )


@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    user = message.from_user
    if not user:
        return

    logger.info("Received /start from user_id=%s (@%s) | args=%r", user.id, user.username, command.args)

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
            "Click a download button from our official channel or open a resource link to begin."
        )
        return

    try:
        await send_resource_result(message, user.id, resource_id)
    except Exception:
        logger.exception("Resource flow failed | user=%s resource=%s", user.id, resource_id)
        await message.answer("⚠️ Something went wrong. Please try again later.")


@dp.callback_query(F.data.startswith("verify:"))
async def verify_callback(callback: CallbackQuery):
    try:
        resource_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError, AttributeError):
        await callback.answer("❌ Invalid resource.", show_alert=True)
        return

    resource = get_resource(resource_id)
    if not resource:
        try:
            await callback.message.edit_text("❌ This resource does not exist or is inactive.")
        except TelegramBadRequest:
            pass
        await callback.answer("❌ Resource not found.", show_alert=True)
        return

    channels = get_required_channels(resource_id)
    total_count = len(channels)
    missing = await verify_user_channels(bot, callback.from_user.id, channels)
    name = resource.get("name", "Anime")
    drive_url = resource.get("drive_url")

    if missing:
        msg_text = format_progress_message(name, total_count, len(missing))
        try:
            await callback.message.edit_text(
                msg_text,
                reply_markup=required_channels_keyboard(missing, total_count, resource_id),
            )
            completed = total_count - len(missing)
            await callback.answer(f"📊 Progress: {completed}/{total_count} channels joined.")
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc):
                await callback.answer(
                    "❌ You still haven't joined the remaining channel(s). Click the join button above first!",
                    show_alert=True,
                )
            else:
                logger.warning("Failed to edit verification message: %s", exc)
        return

    if not drive_url:
        try:
            await callback.message.edit_text("⚠️ Verification passed, but the download link is unavailable.")
        except TelegramBadRequest:
            pass
        await callback.answer("⚠️ Download link unavailable.", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            f"🎉 <b>Verification Successful!</b>\n\n"
            f"🎬 <b>{name}</b>\n\n"
            f"✅ All {total_count} required channel(s) verified!\n\n"
            "Your download link is ready below:",
            reply_markup=download_keyboard(drive_url),
        )
        await callback.answer("🎉 Verification Complete! Enjoy your anime!")
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            await callback.answer("🎉 Already verified!")
        else:
            logger.warning("Failed to edit verification message: %s", exc)


@dp.chat_join_request()
async def chat_join_request_handler(event: ChatJoinRequest):
    """Automatically approve channel join requests so users can pass verification."""
    user = event.from_user
    chat = event.chat
    logger.info(
        "Received Chat Join Request: user_id=%s (@%s) | chat_id=%s ('%s')",
        user.id,
        user.username,
        chat.id,
        chat.title,
    )
    try:
        get_or_create_user(
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    except Exception as exc:
        logger.warning("Failed to save user on join request: %s", exc)

    try:
        await event.approve()
        logger.info("✅ Successfully approved join request for user %s in '%s'", user.id, chat.title)
    except Exception as exc:
        logger.error("❌ Failed to auto-approve join request for user %s in '%s': %s", user.id, chat.title, exc)


@dp.message()
async def fallback_message_handler(message: Message):
    logger.info("Received message: user_id=%s (@%s) | text=%r", message.from_user.id if message.from_user else "unknown", message.from_user.username if message.from_user else "", message.text)
    await message.answer(
        "👋 <b>Welcome to Anime World!</b>\n\n"
        "Click a download button from our official channel or open a resource link to proceed."
    )


async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning("Could not delete webhook: %s", e)

    me = await bot.get_me()
    logger.info("Starting @%s (id=%s)", me.username, me.id)
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
