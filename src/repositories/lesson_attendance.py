from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lesson_attendance import LessonAttendance


class LessonAttendanceRepository:

    def __init__(self, session: AsyncSession):
        self.__session = session

    async def create_attendance(
        self,
        *,
        lesson_code: str,
        user_id: int,
        theory_skips_percentage: float,
        practice_skips_percentage: float,
    ) -> None:
        attendance = LessonAttendance(
            lesson_code=lesson_code,
            user_id=user_id,
            theory_skips_percentage=theory_skips_percentage,
            practice_skips_percentage=practice_skips_percentage,
        )
        self.__session.add(attendance)
        await self.__session.commit()

    async def get_last_attendance(
        self,
        lesson_code: str,
        user_id: int,
    ) -> LessonAttendance | None:
        statement = (
            select(LessonAttendance)
            .where(LessonAttendance.lesson_code == lesson_code, LessonAttendance.user_id == user_id)
            .order_by(LessonAttendance.created_at.desc())
            .limit(1)
        )
        result = await self.__session.execute(statement)
        attendance = result.scalar_one_or_none()
        return attendance
