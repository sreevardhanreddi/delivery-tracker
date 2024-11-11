import os

from telegram import Bot

TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID: str = os.getenv("CHANNEL_ID", "")


async def send_message(message):
    bot = Bot(token=TOKEN)

    await bot.send_message(chat_id=CHAT_ID, text=message)
