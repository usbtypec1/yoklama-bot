import datetime
from dataclasses import dataclass


@dataclass
class LessonGrade:
    id: int
    user_id: int
    lesson_code: str
    exam_name: str
    grade: str | None
    created_at: datetime.datetime
