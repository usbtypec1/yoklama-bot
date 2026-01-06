from dishka import Provider, Scope
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)

from db.engine import get_engine, get_session_factory, get_session
from repositories.user import UserRepository


def db_provider() -> Provider:
    provider = Provider()
    provider.provide(
        source=get_engine,
        provides=AsyncEngine,
        scope=Scope.APP,
    )
    provider.provide(
        source=get_session_factory,
        provides=async_sessionmaker,
        scope=Scope.APP,
    )
    provider.provide(
        source=get_session,
        provides=AsyncSession,
        scope=Scope.REQUEST,
    )
    provider.provide(
        source=UserRepository,
        provides=UserRepository,
        scope=Scope.REQUEST,
    )
    return provider
