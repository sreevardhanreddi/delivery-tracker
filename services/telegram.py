import os

from loguru import logger
from telegram import Bot

TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID: str = os.getenv("CHANNEL_ID", "")


async def send_message(message):
    if not TOKEN or not CHAT_ID:
        logger.warning("Telegram token or chat ID not set")
        return

    bot = Bot(token=TOKEN)

    await bot.send_message(chat_id=CHAT_ID, text=message)
