from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.models.lesson_attendance import (
    LessonAttendance as DatabaseLessonAttendance,
)
from models.obis import LessonAttendance


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
        attendance = DatabaseLessonAttendance(
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
            select(DatabaseLessonAttendance)
            .where(
                DatabaseLessonAttendance.lesson_code == lesson_code,
                DatabaseLessonAttendance.user_id == user_id,
            )
            .options(joinedload(DatabaseLessonAttendance.lesson))
            .order_by(DatabaseLessonAttendance.created_at.desc())
            .limit(1)
        )
        result = await self.__session.execute(statement)
        attendance = result.scalar_one_or_none()
        if attendance is None:
            return None
        return LessonAttendance(
            user_id=attendance.user_id,
            lesson_name=attendance.lesson.name,
            lesson_code=attendance.lesson_code,
            theory_skips_percentage=attendance.theory_skips_percentage,
            practice_skips_percentage=attendance.practice_skips_percentage,
        )
