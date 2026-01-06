from dishka import Provider

from setup.ioc.db import db_provider
from setup.ioc.settings import SettingsProvider
from setup.ioc.telegram_bot import TelegramBotProvider


def get_providers() -> tuple[Provider, ...]:
    return (
        SettingsProvider(),
        TelegramBotProvider(),
        db_provider(),
    )
