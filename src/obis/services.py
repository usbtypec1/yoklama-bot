from obis.models import LessonSkipOpportunity, LessonAttendance


THEORY_SKIPS_THRESHOLD = 30
PRACTICE_SKIPS_THRESHOLD = 20
SKIP_PERCENTAGE_PER_LESSON = 6.25


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
