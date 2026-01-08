from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lesson_grade import LessonGrade as DatabaseLessonGrade
from models.lesson_grade import LessonGrade


class LessonGradeRepository:

    def __init__(self, session: AsyncSession):
        self.__session = session

    async def create_grade(
        self,
        user_id: int,
        lesson_code: str,
        exam_name: str,
        score: str | None,
    ) -> None:
        grade = DatabaseLessonGrade(
            user_id=user_id,
            lesson_code=lesson_code,
            exam_name=exam_name,
            score=score,
        )
        self.__session.add(grade)
        await self.__session.commit()

    async def get_last_grade(
        self,
        lesson_code: str,
        user_id: int,
        exam_name: str,
    ) -> LessonGrade | None:
        statement = (
            select(DatabaseLessonGrade)
            .where(
                DatabaseLessonGrade.lesson_code == lesson_code,
                DatabaseLessonGrade.user_id == user_id,
                DatabaseLessonGrade.exam_name == exam_name,
            )
            .order_by(DatabaseLessonGrade.created_at.desc())
            .limit(1)
        )
        result = await self.__session.scalar(statement)
        if result is None:
            return None
        return LessonGrade(
            id=result.id,
            user_id=result.user_id,
            lesson_code=result.lesson_code,
            exam_name=result.exam_name,
            score=result.score,
            created_at=result.created_at,
        )
