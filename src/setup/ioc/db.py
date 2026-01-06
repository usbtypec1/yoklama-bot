from dishka import Provider, Scope
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)

from db.engine import get_engine


def db_provider() -> Provider:
    provider = Provider()
    provider.provide(
        source=get_engine,
        provides=AsyncEngine,
        scope=Scope.APP,
    )
    provider.provide(
        source=async_sessionmaker,
        provides=async_sessionmaker,
        scope=Scope.APP,
    )
    provider.provide(
        source=async_sessionmaker,
        provides=AsyncSession,
        scope=Scope.REQUEST,
    )
    return provider
