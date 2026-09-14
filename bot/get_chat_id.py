import asyncio
import sys

from aiogram import Bot

from config import TELEGRAM_BOT_TOKEN


async def main():
    if len(sys.argv) != 2:
        print("Usage: python get_chat_id.py @channelusername")
        return
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        me = await bot.get_me()
        chat = await bot.get_chat(sys.argv[1])
        print(f"Bot: @{me.username}")
        print(f"Title: {chat.title}")
        print(f"ID: {chat.id}")
        print(f"Username: {chat.username}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
