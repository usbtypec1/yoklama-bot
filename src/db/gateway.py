import contextlib
import pathlib
from collections.abc import AsyncGenerator
from typing import Final

import aiosqlite

from db.models import UserWithCredentials
from obis.models import LessonAttendance


DATABASE_PATH: Final[pathlib.Path] = (
    pathlib.Path(__file__).parents[3] / "database.db"
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

    async def init_tables(self) -> None:
        queries: tuple[str, ...] = (
            """
            CREATE TABLE IF NOT EXISTS users
            (
                id
                INTEGER
                PRIMARY
                KEY,
                student_number
                TEXT,
                encrypted_password
                TEXT,
                created_at
                TIMESTAMP
                DEFAULT
                CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS lessons
            (
                code
                TEXT
                PRIMARY
                KEY,
                name
                TEXT
                NOT
                NULL
            );
            """,
            """CREATE TABLE IF NOT EXISTS lessons_attendance
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                lesson_code
                TEXT
                NOT
                NULL,
                user_id
                INTEGER
                NOT
                NULL,
                theory_skips_percentage
                REAL,
                practice_skips_percentage
                REAL,
                created_at
                TIMESTAMP
                DEFAULT
                CURRENT_TIMESTAMP,
                FOREIGN
                KEY
               (
                lesson_code
               ) REFERENCES lessons
               (
                   code
               ),
                FOREIGN KEY
               (
                   user_id
               ) REFERENCES users
               (
                   id
               )
                );"""
        )
        for query in queries:
            await self.__connection.execute(query)
        await self.__connection.commit()

    async def get_user_ids(self) -> list[int]:
        query = "SELECT DISTINCT id FROM users"
        async with self.__connection.execute(query) as cursor:
            rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def get_users_with_credentials(self) -> list[UserWithCredentials]:
        query = "SELECT id, student_number, encrypted_password FROM users WHERE student_number IS NOT NULL AND encrypted_password IS NOT NULL"
        async with self.__connection.execute(query) as cursor:
            rows = await cursor.fetchall()
        return [
            UserWithCredentials(
                id=row[0],
                student_number=row[1],
                encrypted_password=row[2],
            )
            for row in rows
        ]

    async def get_user_with_credentials_by_id(
        self,
        user_id: int,
    ) -> UserWithCredentials | None:
        query = "SELECT id, student_number, encrypted_password FROM users WHERE id = ? AND student_number IS NOT NULL AND encrypted_password IS NOT NULL"
        params = (user_id,)
        async with self.__connection.execute(query, params) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return UserWithCredentials(
            id=row[0],
            student_number=row[1],
            encrypted_password=row[2],
        )

    async def create_user(self, user_id: int) -> None:
        query = "INSERT OR IGNORE INTO users (id) VALUES (?)"
        params = (user_id,)
        await self.__connection.execute(query, params)
        await self.__connection.commit()

    async def update_user_credentials(
        self,
        user_id: int,
        student_number: str,
        encrypted_password: str,
    ) -> None:
        query = """
                UPDATE users
                SET student_number     = ?,
                    encrypted_password = ?
                WHERE id = ?;
                """
        params = (student_number, encrypted_password, user_id)
        await self.__connection.execute(query, params)
        await self.__connection.commit()

    async def get_last_lessons_attendance(self, lesson_code: str,
                                          user_id: int) -> LessonAttendance | None:
        query = """
                SELECT lesson_code,
                       lesson_name,
                       theory_skips_percentage,
                       practice_skips_percentage
                FROM lessons_attendance
                WHERE lesson_code = ?
                  AND user_id = ?
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


@contextlib.asynccontextmanager
async def create_database_gateway() -> AsyncGenerator[DatabaseGateway, None]:
    async with create_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        yield gateway
