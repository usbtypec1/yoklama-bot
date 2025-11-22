import logging

from bs4 import BeautifulSoup

from obis.models import LessonAttendance, LessonExams, Exam
from obis.services import try_parse_float


logger = logging.getLogger(__name__)


def parse_taken_grades_page(text: str) -> list[LessonExams]:
    soup = BeautifulSoup(text, "lxml")
    table_bodies = soup.find_all("tbody")
    if not table_bodies:
        return []

    tbody = table_bodies[-1]
    rows = tbody.find_all("tr", recursive=False)

    lessons: list[LessonExams] = []
    i = 0
    exams: list[Exam] = []
    lesson_code = None
    lesson_name = None

    while i < len(rows):
        main_row = rows[i]
        tds = main_row.find_all("td", recursive=False)

        if len(tds) == 5:
            if exams:
                lessons.append(
                    LessonExams(
                        lesson_name=lesson_name, lesson_code=lesson_code,
                        exams=exams,
                    ),
                )
                exams = []

            lesson_code = tds[1].get_text(strip=True) or None
            lesson_name = tds[2].get_text(strip=True) or None

            exam_name = tds[3].get_text(strip=True) or None
            score = tds[4].get_text(strip=True) or None
            exams.append(Exam(name=exam_name, score=score))
        elif len(tds) == 2:
            exam_name = tds[0].get_text(strip=True) or None
            score = tds[1].get_text(strip=True) or None
            exams.append(Exam(name=exam_name, score=score))

        i += 1

    return lessons


def parse_lessons_attendance_page(html: str) -> list[LessonAttendance]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        logger.warning("No attendance table found in the HTML page")
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
