import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka

from handlers import router
from logger import setup_logging
from setup.ioc.registry import get_providers
from setup.settings.app import AppSettings


async def main() -> None:
    settings = AppSettings.from_settings_toml_file()
    container = make_async_container(*get_providers(), context={
        AppSettings: settings,
    })

    bot = await container.get(Bot)

    setup_logging()

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="📲 Главное меню")
        ],
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    setup_dishka(container, router=dispatcher, auto_inject=True)

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
