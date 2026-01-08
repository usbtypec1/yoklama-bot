from collections.abc import Iterable

from models.lesson_grade import LessonGradeChange
from models.obis import LessonAttendance, LessonSkipOpportunity, LessonExams
from services.obis import compute_lesson_skip_opportunities


def inflect_word_skips(count: int) -> str:
    count = abs(count)

    if count % 10 == 1 and count % 100 != 11:
        return "пропуск"
    elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return "пропуска"
    return "пропусков"


def format_lesson_attendance_change(
    old_lesson_attendance: LessonAttendance,
    new_lesson_attendance: LessonAttendance,
    lesson_skip_opportunity: LessonSkipOpportunity,
):
    return (
        f"<b>Ваша йоклама по предмету {old_lesson_attendance.lesson_name} изменилась:\n</b>"
        f"{old_lesson_attendance.theory_skips_percentage} → {new_lesson_attendance.theory_skips_percentage} (осталось {lesson_skip_opportunity.theory} {inflect_word_skips(lesson_skip_opportunity.theory)})\n"
        f"с {old_lesson_attendance.practice_skips_percentage} → {new_lesson_attendance.practice_skips_percentage} (осталось {lesson_skip_opportunity.practice} {inflect_word_skips(lesson_skip_opportunity.practice)})"
    )


def format_exams_list(lessons_exams: Iterable[LessonExams]) -> str:
    lines: list[str] = []
    for lesson_exams in lessons_exams:
        lesson_lines = [
            f"<b>{lesson_exams.lesson_name} ({lesson_exams.lesson_code})</b>"]
        for exam in lesson_exams.exams:
            lesson_lines.append(f" - {exam.name}: {format_none(exam.score)}")
        lines.append("\n".join(lesson_lines))

    if not lines:
        return "У вас нет оценок за экзамены."
    return "\n\n".join(lines)


def format_attendance_list(lessons_attendance: Iterable[LessonAttendance]) -> str:
    lines: list[str] = []
    for lesson_attendance in lessons_attendance:
        skipping = compute_lesson_skip_opportunities(lesson_attendance)
        lesson_name = f"<b>{lesson_attendance.lesson_name}</b>"

        if skipping.practice <= 1 or skipping.theory <= 1:
            lesson_name = f"⚠️ {lesson_name}"
        elif skipping.practice == 0 or skipping.theory == 0:
            lesson_name = f"❗ {lesson_name}"

        lines.append(
            f"{lesson_name}\n"
            f"Теория: {lesson_attendance.theory_skips_percentage}% (осталось {skipping.theory} пропусков)\n"
            f"Практика: {lesson_attendance.practice_skips_percentage}% (осталось {skipping.practice} пропусков)"
        )

    if not lines:
        return "У вас нет предметов."
    return "\n\n".join(lines)


def format_none(value: str | None) -> str:
    return value if value is not None else "-"


def format_lesson_grade_change(
    lesson_grade_change: LessonGradeChange,
) -> str:
    if lesson_grade_change.is_first_grade:
        return (
            f"Новая оценка по предмету: {lesson_grade_change.lesson_name} - {format_none(lesson_grade_change.current_score)}"
        )
    return (
        f"Ваша оценка по предмету {lesson_grade_change.lesson_name} изменилась: "
        f"{format_none(lesson_grade_change.previous_score)} → {format_none(lesson_grade_change.current_score)}"
    )
