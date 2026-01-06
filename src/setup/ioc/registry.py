from dishka import Provider

from setup.ioc.db import DBProvider
from setup.ioc.settings import SettingsProvider
from setup.ioc.telegram_bot import TelegramBotProvider


def get_providers() -> tuple[Provider, ...]:
    return (
        SettingsProvider(),
        TelegramBotProvider(),
        DBProvider(),
    )
