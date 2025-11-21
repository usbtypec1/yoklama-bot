from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.exceptions import TelegramApiError

from database_gateway import DatabaseGateway, get_database_connection

BOT_TOKEN = ""
TEXT = ""


async def main():
    bot: Bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )
    
    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        user_ids = gateway.get_user_ids()
    
    async with bot:
        
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=TEXT,
                )
            except TelegramApiError:
                pass