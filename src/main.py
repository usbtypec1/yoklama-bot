import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka

from crypto import PasswordCryptor
from handlers import router
from logger import setup_logging
from periodic_tasks import LessonAttendanceCheckTask
from setup.ioc.registry import get_providers
from setup.settings.app import AppSettings


async def main() -> None:
    settings = AppSettings.from_settings_toml_file()
    container = make_async_container(*get_providers(), context={
        AppSettings: settings,
    })

    bot = await container.get(Bot)

    setup_logging()

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

    setup_dishka(container, router=dispatcher, auto_inject=True)

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
