import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import load_settings
from crypto import PasswordCryptor
from db.gateway import create_database_gateway
from handlers import router
from logger import setup_logging
from periodic_tasks import LessonAttendanceCheckTask


async def main() -> None:
    setup_logging()
    async with create_database_gateway() as db_gateway:
        await db_gateway.init_tables()

    settings = load_settings()
    bot = Bot(
        token=settings.telegram_bot.token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )
    password_cryptor = PasswordCryptor(
        settings.cryptography.secret_key.get_secret_value(),
    )
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="📲 Главное меню")
        ],
    )
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        LessonAttendanceCheckTask(
            bot=bot, password_cryptor=password_cryptor,
        ).execute,
        IntervalTrigger(minutes=15),
    )

    dispatcher = Dispatcher()
    dispatcher["password_cryptor"] = password_cryptor
    dispatcher.include_router(router)

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
