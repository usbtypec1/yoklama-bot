import logging
from collections.abc import AsyncGenerator
from typing import NewType, Final

import httpx
from bs4 import BeautifulSoup

from exceptions.obis import ObisClientNotLoggedInError
from models.obis import (
    LessonAttendance,
    LessonSkipOpportunity,
    Exam,
    LessonExams,
)


log = logging.getLogger(__name__)

ObisHttpClient = NewType("ObisHttpClient", httpx.AsyncClient)


async def get_obis_http_client() -> AsyncGenerator[ObisHttpClient, None]:
    async with httpx.AsyncClient(
        base_url="https://obistest.manas.edu.kg/",
        headers={"User-Agent": "Yoklama parser"},
        timeout=30,
        follow_redirects=True,
    ) as http_client:
        yield ObisHttpClient(http_client)


THEORY_SKIPS_THRESHOLD: Final[int] = 30
PRACTICE_SKIPS_THRESHOLD: Final[int] = 20
SKIP_PERCENTAGE_PER_LESSON: Final[float] = 6.25


def compute_lesson_skip_opportunities(
    lesson: LessonAttendance,
) -> LessonSkipOpportunity:
    if lesson.theory_skips_percentage is not None:
        diff = (
            THEORY_SKIPS_THRESHOLD - lesson.theory_skips_percentage
        )
        if diff == SKIP_PERCENTAGE_PER_LESSON:
            theory_skippable_lessons_count = 0
        else:
            theory_skippable_lessons_count = int(
                diff // SKIP_PERCENTAGE_PER_LESSON,
            )
    else:
        theory_skippable_lessons_count = None
    if lesson.practice_skips_percentage is not None:
        diff = (
            PRACTICE_SKIPS_THRESHOLD
            - lesson.practice_skips_percentage
        )
        if diff == SKIP_PERCENTAGE_PER_LESSON:
            practice_skippable_lessons_count = 0
        else:
            practice_skippable_lessons_count = int(
                diff // SKIP_PERCENTAGE_PER_LESSON,
            )
    else:
        practice_skippable_lessons_count = None

    return LessonSkipOpportunity(
        theory=theory_skippable_lessons_count,
        practice=practice_skippable_lessons_count,
    )


def try_parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_taken_grades_page(text: str) -> list[LessonExams]:
    soup = BeautifulSoup(text, "lxml")
    table_bodies = soup.find_all("tbody")
    if not table_bodies:
        return []

    tbody = table_bodies[-1]
    rows = tbody.find_all("tr", recursive=False)

    lessons: list[LessonExams] = []
    i = 0

    while i < len(rows):
        main_row = rows[i]
        tds = main_row.find_all("td", recursive=False)

        print(tds, len(tds))

        if len(tds) == 5:
            # This is a new lesson row
            lesson_code = tds[1].get_text(strip=True) or None
            lesson_name = tds[2].get_text(strip=True) or None

            # Get rowspan from first column to determine how many rows belong to this lesson
            rowspan = int(tds[0].get('rowspan', 1))

            # Collect all exams for this lesson
            exams: list[Exam] = []

            # First exam from the current row
            exam_name = tds[3].get_text(strip=True) or None
            score = tds[4].get_text(strip=True) or None
            exams.append(Exam(name=exam_name, score=score))

            # Process additional rows if rowspan > 1
            for j in range(1, rowspan):
                if i + j < len(rows):
                    next_row = rows[i + j]
                    next_tds = next_row.find_all("td", recursive=False)

                    if len(next_tds) == 2:
                        exam_name = next_tds[0].get_text(strip=True) or None
                        score = next_tds[1].get_text(strip=True) or None
                        exams.append(Exam(name=exam_name, score=score))

            # Add the lesson with all its exams
            lessons.append(
                LessonExams(
                    lesson_name=lesson_name,
                    lesson_code=lesson_code,
                    exams=exams,
                )
            )

            # Skip the rows we've already processed
            i += rowspan
        else:
            # Skip any orphaned rows that don't match expected structure
            i += 1

    return lessons

def parse_lessons_attendance_page(html: str) -> list[LessonAttendance]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        log.warning("No attendance table found in the HTML page")
        return []
    table_rows = table.find_all("tr")[1:]
    lessons: list[LessonAttendance] = []
    for table_row in table_rows:
        tds = table_row.find_all("td")
        if len(tds) != 9:
            continue
        lesson_name = tds[2].get_text(strip=True)
        lesson_code = tds[1].get_text(strip=True)
        theory_skips_percentage = tds[4].text.strip("% ")
        practice_skips_percentage = tds[6].text.strip(
            "% ",
        )

        lesson = LessonAttendance(
            lesson_name=lesson_name,
            lesson_code=lesson_code,
            theory_skips_percentage=try_parse_float(
                theory_skips_percentage,
            ),
            practice_skips_percentage=try_parse_float(
                practice_skips_percentage,
            ),
        )
        lessons.append(lesson)
    return lessons


class ObisService:

    def __init__(self, http_client: ObisHttpClient):
        self.__http_client = http_client

    async def login(
        self,
        student_number: str,
        password: str,
    ) -> None:
        url = "/site/login"
        response = await self.__http_client.get(url)

        soup = BeautifulSoup(response.text, "lxml")

        csrf_input = soup.find("input", {"name": "_csrf"})
        if csrf_input is None:
            log.error("ObisClient login: CSRF token not found")
            return

        csrf_token = csrf_input.get("value")
        if csrf_token is None:
            log.error("ObisClient login: CSRF token value not found")
            return

        request_data = {
            "_csrf": csrf_token,
            "LoginForm[username]": student_number,
            "LoginForm[password_hash]": password,
        }
        response = await self.__http_client.post(url, data=request_data)
        if '/site/login' in response.text or response.is_error:
            log.error(
                "ObisClient login: login failed for student number %s",
                student_number,
            )
            raise ObisClientNotLoggedInError

    async def get_lessons_attendance(self) -> list[LessonAttendance]:
        url = "/vs-ders/taken-lessons"
        response = await self.__http_client.get(url)
        return parse_lessons_attendance_page(response.text)

    async def get_lesson_exams(self) -> list[LessonExams]:
        url = "/vs-ders/taken-grades"
        response = await self.__http_client.get(url)
        return parse_taken_grades_page(response.text)
