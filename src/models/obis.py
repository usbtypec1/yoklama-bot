from dataclasses import dataclass

from pydantic import BaseModel


class LessonAttendance(BaseModel):
    user_id: int
    lesson_name: str
    lesson_code: str
    theory_skips_percentage: float | None
    practice_skips_percentage: float | None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LessonAttendance):
            return NotImplemented
        return (
            self.user_id == other.user_id and
            self.lesson_code == other.lesson_code and
            self.theory_skips_percentage == other.theory_skips_percentage and
            self.practice_skips_percentage == other.practice_skips_percentage
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class LessonAttendanceChange:
    previous: LessonAttendance | None
    current: LessonAttendance


class LessonSkipOpportunity(BaseModel):
    theory: int | None
    practice: int | None


class Exam(BaseModel):
    name: str
    score: str | None


class LessonExams(BaseModel):
    lesson_name: str
    lesson_code: str
    exams: list[Exam]
