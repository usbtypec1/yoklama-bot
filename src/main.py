import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka
from sqlalchemy.ext.asyncio import AsyncEngine

from db.models.base import Base
from handlers import router
from logger import setup_logging
from periodic_tasks import LessonAttendanceCheckTask, LessonGradeSyncTask
from setup.ioc.registry import get_providers
from setup.settings.app import AppSettings


async def main() -> None:
    settings = AppSettings.from_settings_toml_file()
    container = make_async_container(
        *get_providers(), context={
            AppSettings: settings,
        },
    )

    bot = await container.get(Bot)

    setup_logging()

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="📲 Главное меню")
        ],
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        LessonAttendanceCheckTask(container).execute,
        IntervalTrigger(minutes=5),
    )
    scheduler.add_job(
        LessonGradeSyncTask(container).execute,
        IntervalTrigger(minutes=30),
    )
    scheduler.start()

    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    setup_dishka(container, router=dispatcher, auto_inject=True)

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
