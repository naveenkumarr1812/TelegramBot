import asyncio
import os

from aiogram import Bot
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def main():
    bot = Bot(token=BOT_TOKEN)

    try:
        me = await bot.get_me()

        print(f"Bot: @{me.username}")

        # Replace with your channel username
        chat = await bot.get_chat("@YOUR_CHANNEL_USERNAME")

        print("Channel information")
        print("-------------------")
        print("Title:", chat.title)
        print("ID:", chat.id)
        print("Username:", chat.username)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())