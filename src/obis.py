import contextlib
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Callable, NewType

import httpx
from bs4 import BeautifulSoup

from database_gateway import Lesson


ObisHttpClient = NewType("ObisHttpClient", httpx.AsyncClient)


class ObisClientNotLoggedInError(Exception):
    pass


def compare_lessons(
    old_lessons: list[Lesson], new_lessons: list[Lesson]
) -> list[tuple[Lesson, Lesson]]:
    new_lesson_name_to_lesson = {lesson.name: lesson for lesson in new_lessons}

    changed_lessons = []
    for old_lesson in old_lessons:
        new_lesson = new_lesson_name_to_lesson.get(old_lesson.name)
        if new_lesson is None:
            continue
        if old_lesson != new_lesson:
            changed_lessons.append((old_lesson, new_lesson))

    return changed_lessons


THREORY_SKIPS_THRESHOLD = 30
PRACTICE_SKIPS_THRESHOLD = 20
SKIP_PERCENTAGE_PER_LESSON = 6.25


@dataclass(slots=True, kw_only=True, frozen=True)
class LessonSkippingOpportunity:
    theory: int | None
    practice: int | None


@dataclass(slots=True, kw_only=True, frozen=True)
class Exam:
    name: str
    score: str | None


@dataclass(slots=True, kw_only=True, frozen=True)
class LessonExams:
    lesson_name: str
    lesson_code: str
    exams: list[Exam]


def parse_taken_grades_page(text: str) -> list[LessonExams]:
    soup = BeautifulSoup(text, "lxml")
    tbodies = soup.find_all("tbody")
    if not tbodies:
        return []

    tbody = tbodies[-1]
    rows = tbody.find_all("tr", recursive=False)

    lessons: list[LessonExams] = []
    i = 0
    exams: list[Exam] = []
    lesson_code = None
    lesson_name = None

    while i < len(rows):
        main_row = rows[i]
        tds = main_row.find_all("td", recursive=False)

        # only the "main" row contains >=5 tds (index, code, name, exam, score)
        if len(tds) == 5:
            print(exams)
            if exams:
                lessons.append(
                    LessonExams(
                        lesson_name=lesson_name, lesson_code=lesson_code, exams=exams
                    )
                )
                exams = []

            lesson_code = tds[1].get_text(strip=True) or None
            lesson_name = tds[2].get_text(strip=True) or None

            exam_name = tds[3].get_text(strip=True) or None
            score = tds[4].get_text(strip=True) or None
            exams.append(Exam(name=exam_name, score=score))
        elif len(tds) == 2:
            print(exams)
            exam_name = tds[0].get_text(strip=True) or None
            score = tds[1].get_text(strip=True) or None
            exams.append(Exam(name=exam_name, score=score))

        i += 1

    return lessons


def compute_lesson_skipping_opportunities(
    lesson: Lesson,
) -> LessonSkippingOpportunity:
    if lesson.theory_skipped_classes_percentage is not None:
        diff = THREORY_SKIPS_THRESHOLD - lesson.theory_skipped_classes_percentage
        if diff == SKIP_PERCENTAGE_PER_LESSON:
            theory_skippable_lessons_count = 0
        else:
            theory_skippable_lessons_count = int(
                diff // SKIP_PERCENTAGE_PER_LESSON,
            )
    else:
        theory_skippable_lessons_count = None
    if lesson.practice_skipped_classes_percentage is not None:
        diff = PRACTICE_SKIPS_THRESHOLD - lesson.practice_skipped_classes_percentage
        if diff == SKIP_PERCENTAGE_PER_LESSON:
            practice_skippable_lessons_count = 0
        else:
            practice_skippable_lessons_count = int(
                diff // SKIP_PERCENTAGE_PER_LESSON,
            )
    else:
        practice_skippable_lessons_count = None

    return LessonSkippingOpportunity(
        theory=theory_skippable_lessons_count,
        practice=practice_skippable_lessons_count,
    )


@contextlib.asynccontextmanager
async def create_http_client() -> AsyncGenerator[ObisHttpClient, None]:
    async with httpx.AsyncClient(
        base_url="https://obistest.manas.edu.kg/",
        headers={"User-Agent": "Yoklama parser"},
        timeout=30,
        follow_redirects=True,
    ) as http_client:
        yield ObisHttpClient(http_client)


def login_required[T, **P](f: Callable[P, T]) -> Callable[P, T]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        obj = args[0]
        if not obj.is_logged_in:
            raise ObisClientNotLoggedInError
        return f(*args, **kwargs)

    return inner


def try_parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


@dataclass(slots=True, kw_only=True)
class ObisClient:
    student_number: str
    password: str
    http_client: ObisHttpClient
    is_logged_in: bool = False

    async def login(self) -> None:
        if self.is_logged_in:
            return
        url = "/site/login"
        response = await self.http_client.get(url)

        soup = BeautifulSoup(response.text, "lxml")
        csrf_input = soup.find("input", {"name": "_csrf"})
        if csrf_input is None:
            return
        csrf_token = csrf_input.get("value")
        if csrf_token is None:
            return
        request_data = {
            "_csrf": csrf_token,
            "LoginForm[username]": self.student_number,
            "LoginForm[password_hash]": self.password,
        }
        response = await self.http_client.post(url, data=request_data)
        if response.is_success:
            self.is_logged_in = True

    @login_required
    async def get_taken_grades_page(self) -> list[LessonExams]:
        url = "/vs-ders/taken-grades"
        response = await self.http_client.get(url)
        return parse_taken_grades_page(response.text)

    @login_required
    async def get_taken_lessons_page(self) -> list[Lesson]:
        url = "/vs-ders/taken-lessons"
        response = await self.http_client.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")
        if table is None:
            return []
        table_rows = table.find_all("tr")[1:]
        lessons: list[Lesson] = []
        for table_row in table_rows:
            tds = table_row.find_all("td")
            if len(tds) != 8:
                continue
            lesson_name = tds[2].text.strip()
            theory_lessons_skipped_classes_percentage = tds[4].text.strip("% ")
            practice_lessons_skipped_classes_percentage = tds[6].text.strip(
                "% ",
            )

            lesson = Lesson(
                name=lesson_name,
                theory_skipped_classes_percentage=try_parse_float(
                    theory_lessons_skipped_classes_percentage,
                ),
                practice_skipped_classes_percentage=try_parse_float(
                    practice_lessons_skipped_classes_percentage,
                ),
            )
            lessons.append(lesson)
        return lessons
