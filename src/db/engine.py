import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)


log = logging.getLogger(__name__)


@asynccontextmanager
async def get_engine(
    database_url: PostgresDsn,
) -> AsyncGenerator[AsyncEngine, None]:
    log.debug("Database engine factory: creating engine")
    engine = create_async_engine(str(database_url))
    log.debug("Database engine factory: engine created")
    try:
        yield engine
    finally:
        log.debug("Database engine factory: disposing engine")
        await engine.dispose()
        log.debug("Database engine factory: engine disposed")


def get_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine)


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    log.debug("Session factory: creating session")
    async with session_factory() as session:
        log.debug("Session factory: session created")
        yield session
        log.debug("Session factory: session closed")
