import contextlib
import pathlib
import sqlite3
from collections.abc import Generator
from dataclasses import dataclass


@dataclass(slots=True, kw_only=True, frozen=True)
class Lesson:
    name: str
    theory_skipped_classes_percentage: float | None
    practice_skipped_classes_percentage: float | None


@dataclass(slots=True, kw_only=True, frozen=True)
class UserWithCredentials:
    id: int
    student_number: str
    password: str


DATABASE_FILE = pathlib.Path(__file__).parent.parent / "database.db"


@contextlib.contextmanager
def get_database_connection() -> Generator[sqlite3.Connection, None, None]:
    with sqlite3.connect(DATABASE_FILE) as connection:
        yield connection


@dataclass(slots=True, frozen=True)
class DatabaseGateway:
    connection: sqlite3.Connection
    
    def get_user_ids(self) -> list[int]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM users;")
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    def get_user_by_id(self, user_id: int) -> UserWithCredentials | None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, student_number, password
            FROM users
            WHERE id = ?;
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if row[1] is None or row[2] is None:
            return None
        return UserWithCredentials(
            id=row[0],
            student_number=row[1],
            password=row[2],
        )

    def get_users_with_credentials(self) -> list[UserWithCredentials]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, student_number, password
            FROM users
            WHERE student_number IS NOT NULL
              AND password IS NOT NULL;
            """,
        )
        rows = cursor.fetchall()
        return [
            UserWithCredentials(
                id=row[0],
                student_number=row[1],
                password=row[2],
            )
            for row in rows
        ]

    def init_tables(self) -> None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY,
                    student_number
                    TEXT,
                    password
                    TEXT,
                    created_at
                    TIMESTAMP
                    DEFAULT
                    CURRENT_TIMESTAMP
                )
                """,
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS lessons
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    user_id
                    INTEGER,
                    name
                    TEXT
                    NOT
                    NULL,
                    theory_skipped_classes_percentage
                    REAL,
                    practice_skipped_classes_percentage
                    REAL,
                    updated_at
                    TIMESTAMP
                    DEFAULT
                    CURRENT_TIMESTAMP,
                    FOREIGN
                    KEY
                (
                    user_id
                ) REFERENCES users
                (
                    id
                ),
                    UNIQUE
                (
                    user_id,
                    name
                )
                    )
                """,
            )

    def insert_user(self, user_id: int) -> None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO users (id) VALUES (?) ON CONFLICT DO NOTHING",
                (user_id,),
            )

    def update_user_credentials(self, user_id: int, student_number: str,
                                password: str) -> None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE users
                SET student_number = ?,
                    password       = ?
                WHERE id = ?
                """,
                (student_number, password, user_id),
            )

    def upsert_lesson(self, user_id: int, lesson: Lesson) -> None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO lessons (user_id, name,
                                     theory_skipped_classes_percentage,
                                     practice_skipped_classes_percentage)
                VALUES (?, ?, ?, ?) ON CONFLICT (user_id, name) DO
                UPDATE SET
                    theory_skipped_classes_percentage = EXCLUDED.theory_skipped_classes_percentage,
                    practice_skipped_classes_percentage = EXCLUDED.practice_skipped_classes_percentage,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    lesson.name,
                    lesson.theory_skipped_classes_percentage,
                    lesson.practice_skipped_classes_percentage,
                ),
            )

    def get_lessons(self, user_id: int) -> list[Lesson]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name, theory_skipped_classes_percentage, practice_skipped_classes_percentage FROM lessons WHERE user_id = ?",
            (user_id,),
        )
        rows = cursor.fetchall()
        return [
            Lesson(
                name=row[0],
                theory_skipped_classes_percentage=row[1],
                practice_skipped_classes_percentage=row[2],
            )
            for row in rows
        ]
