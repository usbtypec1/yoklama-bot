import contextlib
import pathlib
from collections.abc import AsyncGenerator
from typing import Final

import aiosqlite

from models.user import User
from obis.models import LessonAttendance


DATABASE_PATH: Final[pathlib.Path] = (
    pathlib.Path(__file__).parents[2] / "database.db"
)


@contextlib.asynccontextmanager
async def create_database_connection() -> AsyncGenerator[
    aiosqlite.Connection, None]:
    async with aiosqlite.connect(DATABASE_PATH) as connection:
        await connection.execute("PRAGMA foreign_keys = ON;")
        yield connection


class DatabaseGateway:

    def __init__(self, connection: aiosqlite.Connection):
        self.__connection = connection

    async def get_users_with_credentials(self) -> list[User]:
        query = "SELECT id, student_number, encrypted_password FROM users WHERE student_number IS NOT NULL AND encrypted_password IS NOT NULL"
        async with self.__connection.execute(query) as cursor:
            rows = await cursor.fetchall()
        return [
            User(
                id=row[0],
                student_number=row[1],
                encrypted_password=row[2],
            )
            for row in rows
        ]

    async def get_last_lessons_attendance(self, lesson_code: str,
                                          user_id: int) -> LessonAttendance | None:
        query = """
                SELECT la.lesson_code,
                       l.name,
                       la.theory_skips_percentage,
                       la.practice_skips_percentage
                FROM lessons_attendance la
                         JOIN lessons l ON l.code = la.lesson_code
                WHERE la.lesson_code = ?
                  AND la.user_id = ?
                ORDER BY created_at DESC LIMIT 1 \
                """
        params = (lesson_code, user_id)
        async with self.__connection.execute(query, params) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return LessonAttendance(
            lesson_code=row[0],
            lesson_name=row[1],
            theory_skips_percentage=row[2],
            practice_skips_percentage=row[3],
        )

    async def create_lesson_attendance(
        self,
        lesson_attendance: LessonAttendance,
        user_id: int,
    ) -> None:
        query = """
                INSERT
                OR IGNORE INTO lessons
                (code, name)
                VALUES (?, ?);"""
        params = (lesson_attendance.lesson_code,
                  lesson_attendance.lesson_name)
        await self.__connection.execute(query, params)
        await self.__connection.commit()
        query = """
                INSERT INTO lessons_attendance
                (lesson_code,
                 user_id,
                 theory_skips_percentage,
                 practice_skips_percentage)
                VALUES (?, ?, ?, ?);
                """
        params = (
            lesson_attendance.lesson_code,
            user_id,
            lesson_attendance.theory_skips_percentage,
            lesson_attendance.practice_skips_percentage,
        )
        await self.__connection.execute(query, params)
        await self.__connection.commit()

    async def clear_user_credentials(self, user_id: int) -> None:
        query = """
                UPDATE users
                SET student_number     = NULL,
                    encrypted_password = NULL
                WHERE id = ?;
                """
        params = (user_id,)
        await self.__connection.execute(query, params)
        await self.__connection.commit()


@contextlib.asynccontextmanager
async def create_database_gateway() -> AsyncGenerator[DatabaseGateway, None]:
    async with create_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        yield gateway
