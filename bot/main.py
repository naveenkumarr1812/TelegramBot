import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery

from config import TELEGRAM_BOT_TOKEN

from database import supabase

from services import (
    parse_resource_parameter,
    get_resource,
    get_required_channels,
)

from verification import verify_user_channels

from keyboards import required_channels_keyboard

from users import save_user


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# BOT
# ============================================================

bot = Bot(
    token=TELEGRAM_BOT_TOKEN
)

dp = Dispatcher()


# ============================================================
# SAVE VERIFICATION LOG
# ============================================================

def save_verification_log(
    telegram_user_id: int,
    resource_id: int,
    verified: bool,
    missing_channels: list,
) -> None:
    """
    Save the verification attempt into Supabase.
    """

    missing = [
        {
            "id": channel["id"],
            "name": channel["name"],
        }
        for channel in missing_channels
    ]

    try:

        (
            supabase
            .table("verification_logs")
            .insert(
                {
                    "telegram_user_id": telegram_user_id,
                    "resource_id": resource_id,
                    "verified": verified,
                    "missing_channels": missing,
                }
            )
            .execute()
        )

    except Exception as error:

        logger.error(
            "Failed to save verification log: %s",
            error,
        )


# ============================================================
# PROCESS VERIFICATION
# ============================================================

async def process_verification(
    user_id: int,
    resource_id: int,
) -> dict:
    """
    Verify whether a Telegram user has joined
    all channels required for a resource.

    Returns a dictionary containing either:

        {
            "success": True,
            "resource": resource
        }

    or:

        {
            "success": False,
            "resource": resource,
            "missing_channels": [...]
        }

    or:

        {
            "success": False,
            "message": "..."
        }
    """

    # --------------------------------------------------------
    # Get resource
    # --------------------------------------------------------

    resource = get_resource(
        resource_id
    )

    if not resource:

        return {
            "success": False,
            "message": (
                "❌ Resource not found "
                "or is inactive."
            ),
        }

    # --------------------------------------------------------
    # Get required channels
    # --------------------------------------------------------

    channels = get_required_channels(
        resource_id
    )

    logger.info(
        "Resource %s requires %s channel(s)",
        resource_id,
        len(channels),
    )

    # --------------------------------------------------------
    # Verify membership
    # --------------------------------------------------------

    missing_channels = await verify_user_channels(
        bot=bot,
        user_id=user_id,
        channels=channels,
    )

    # --------------------------------------------------------
    # User has NOT joined all channels
    # --------------------------------------------------------

    if missing_channels:

        logger.info(
            "User %s is missing %s channel(s)",
            user_id,
            len(missing_channels),
        )

        save_verification_log(
            telegram_user_id=user_id,
            resource_id=resource_id,
            verified=False,
            missing_channels=missing_channels,
        )

        return {
            "success": False,
            "resource": resource,
            "missing_channels": missing_channels,
        }

    # --------------------------------------------------------
    # User has joined all required channels
    # --------------------------------------------------------

    logger.info(
        "User %s successfully verified for resource %s",
        user_id,
        resource_id,
    )

    save_verification_log(
        telegram_user_id=user_id,
        resource_id=resource_id,
        verified=True,
        missing_channels=[],
    )

    return {
        "success": True,
        "resource": resource,
    }


# ============================================================
# /START HANDLER
# ============================================================

@dp.message(CommandStart())
async def start_handler(
    message: Message,
    command: CommandObject,
) -> None:
    """
    Handles:

        /start

    and Telegram deep links such as:

        /start resource_1
    """

    user = message.from_user

    if not user:
        return

    # --------------------------------------------------------
    # Save/update user
    # --------------------------------------------------------

    try:

        save_user(user)

    except Exception as error:

        logger.error(
            "Failed to save user %s: %s",
            user.id,
            error,
        )

    # --------------------------------------------------------
    # Get deep-link parameter
    # --------------------------------------------------------

    parameter = command.args

    logger.info(
        "User %s started bot with parameter: %s",
        user.id,
        parameter,
    )

    # --------------------------------------------------------
    # Normal /start
    # --------------------------------------------------------

    if not parameter:

        await message.answer(
            "👋 Welcome to Anime World!\n\n"
            "Use the download button from our "
            "anime channels to access a resource."
        )

        return

    # --------------------------------------------------------
    # Parse resource parameter
    # --------------------------------------------------------

    resource_id = parse_resource_parameter(
        parameter
    )

    if not resource_id:

        await message.answer(
            "❌ Invalid resource link.\n\n"
            "Please use the download link provided "
            "in the Anime World channel."
        )

        return

    # --------------------------------------------------------
    # Process verification
    # --------------------------------------------------------

    try:

        result = await process_verification(
            user_id=user.id,
            resource_id=resource_id,
        )

    except Exception as error:

        logger.exception(
            "Verification error for user %s: %s",
            user.id,
            error,
        )

        await message.answer(
            "⚠️ Something went wrong while "
            "checking your membership.\n\n"
            "Please try again later."
        )

        return

    # --------------------------------------------------------
    # Resource not found / error
    # --------------------------------------------------------

    if (
        not result["success"]
        and "missing_channels" not in result
    ):

        await message.answer(
            result["message"]
        )

        return

    # --------------------------------------------------------
    # Verification successful
    # --------------------------------------------------------

    if result["success"]:

        resource = result["resource"]

        resource_name = resource.get(
            "name",
            "Your resource",
        )

        drive_url = resource.get(
            "drive_url"
        )

        if not drive_url:

            await message.answer(
                "⚠️ The download link for this "
                "resource is currently unavailable."
            )

            return

        await message.answer(
            "✅ Verification Successful!\n\n"
            f"📦 {resource_name}\n\n"
            "🔗 Your download link:\n"
            f"{drive_url}"
        )

        return

    # --------------------------------------------------------
    # Verification failed
    # --------------------------------------------------------

    missing_channels = result[
        "missing_channels"
    ]

    await message.answer(
        "🔐 Verification Required\n\n"
        "You need to join the following "
        "channel(s) first:\n\n"
        "1️⃣ Click each channel button below.\n"
        "2️⃣ Join the channel.\n"
        "3️⃣ Come back and click "
        "🔄 Verify Again.",
        reply_markup=required_channels_keyboard(
            channels=missing_channels,
            resource_id=resource_id,
        ),
    )


# ============================================================
# VERIFY AGAIN CALLBACK
# ============================================================

@dp.callback_query(
    F.data.startswith("verify:")
)
async def verify_callback(
    callback: CallbackQuery,
) -> None:
    """
    Handles the:

        🔄 Verify Again

    button.

    Callback format:

        verify:123

    where 123 is the resource ID.
    """

    # --------------------------------------------------------
    # Validate callback data
    # --------------------------------------------------------

    if not callback.data:

        await callback.answer(
            "❌ Invalid verification request.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Extract resource ID
    # --------------------------------------------------------

    try:

        resource_id = int(
            callback.data.split(
                ":",
                1
            )[1]
        )

    except (ValueError, IndexError):

        await callback.answer(
            "❌ Invalid resource.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Show loading message in Telegram
    # --------------------------------------------------------

    await callback.answer(
        "🔍 Checking your membership..."
    )

    # --------------------------------------------------------
    # Verify again
    # --------------------------------------------------------

    try:

        result = await process_verification(
            user_id=callback.from_user.id,
            resource_id=resource_id,
        )

    except Exception as error:

        logger.exception(
            "Verification error for user %s: %s",
            callback.from_user.id,
            error,
        )

        try:

            await callback.message.edit_text(
                "⚠️ Something went wrong while "
                "checking your membership.\n\n"
                "Please try again."
            )

        except Exception:

            await callback.message.answer(
                "⚠️ Something went wrong while "
                "checking your membership.\n\n"
                "Please try again."
            )

        return

    # --------------------------------------------------------
    # Resource not found
    # --------------------------------------------------------

    if (
        not result["success"]
        and "missing_channels" not in result
    ):

        await callback.message.edit_text(
            result["message"]
        )

        return

    # --------------------------------------------------------
    # Verification successful
    # --------------------------------------------------------

    if result["success"]:

        resource = result["resource"]

        resource_name = resource.get(
            "name",
            "Your resource",
        )

        drive_url = resource.get(
            "drive_url"
        )

        if not drive_url:

            await callback.message.edit_text(
                "⚠️ The download link for this "
                "resource is currently unavailable."
            )

            return

        await callback.message.edit_text(
            "✅ Verification Successful!\n\n"
            f"📦 {resource_name}\n\n"
            "🔗 Your download link:\n"
            f"{drive_url}"
        )

        return

    # --------------------------------------------------------
    # Still missing channels
    # --------------------------------------------------------

    missing_channels = result[
        "missing_channels"
    ]

    await callback.message.edit_text(
        "❌ You haven't joined all the "
        "required channels yet.\n\n"
        "Please join the channels below "
        "and click 🔄 Verify Again.",
        reply_markup=required_channels_keyboard(
            channels=missing_channels,
            resource_id=resource_id,
        ),
    )


# ============================================================
# START BOT
# ============================================================

async def main():

    logger.info(
        "Starting Anime World Bot..."
    )

    try:

        # ----------------------------------------------------
        # Get bot information
        # ----------------------------------------------------

        bot_info = await bot.get_me()

        logger.info(
            "Bot started successfully: @%s",
            bot_info.username,
        )

        # ----------------------------------------------------
        # Start polling
        # ----------------------------------------------------

        await dp.start_polling(
            bot
        )

    finally:

        await bot.session.close()

        logger.info(
            "Bot session closed."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot stopped by user."
        )