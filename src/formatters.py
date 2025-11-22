from obis.models import LessonAttendance, LessonSkipOpportunity


def format_lesson_attendance_change(
    old_lesson_attendance: LessonAttendance,
    new_lesson_attendance: LessonAttendance,
    lesson_skip_opportunity: LessonSkipOpportunity,
):
    return (
        f"<b>Ваша йоклама по предмету {old_lesson_attendance.lesson_name} изменилась:\n</b>"
        f"{old_lesson_attendance.theory_skips_percentage} → {new_lesson_attendance.theory_skips_percentage} (осталось {lesson_skip_opportunity.theory} пропусков)\n"
        f"с {old_lesson_attendance.practice_skips_percentage} → {new_lesson_attendance.practice_skips_percentage} (осталось {lesson_skip_opportunity.practice} пропусков)"
    )
