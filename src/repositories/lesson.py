from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lesson import Lesson


class LessonRepository:

    def __init__(self, session: AsyncSession):
        self.__session = session

    async def create_lesson(self, code: str, name: str) -> None:
        statement = (
            insert(Lesson)
            .values(code=code, name=name)
            .on_conflict_do_nothing()
        )
        await self.__session.execute(statement)
        await self.__session.commit()
