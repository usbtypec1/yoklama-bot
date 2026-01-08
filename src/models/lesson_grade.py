import datetime
from dataclasses import dataclass


@dataclass
class LessonGrade:
    id: int
    user_id: int
    lesson_code: str
    exam_name: str
    score: str | None
    created_at: datetime.datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class LessonGradeChange:
    user_id: int
    lesson_code: str
    lesson_name: str
    exam_name: str
    previous_score: str | None
    current_score: str | None
    is_first_grade: bool
