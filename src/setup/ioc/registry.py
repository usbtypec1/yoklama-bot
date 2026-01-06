from dishka import Provider

from setup.ioc.db import DBProvider
from setup.ioc.settings import SettingsProvider


def get_providers() -> tuple[Provider, ...]:
    return (
        SettingsProvider(),
        DBProvider(),
    )
