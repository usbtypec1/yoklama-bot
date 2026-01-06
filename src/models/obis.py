from pydantic import BaseModel


class LessonAttendance(BaseModel):
    lesson_name: str
    lesson_code: str
    theory_skips_percentage: float | None
    practice_skips_percentage: float | None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LessonAttendance):
            return NotImplemented
        return (
            self.lesson_code == other.lesson_code and
            self.theory_skips_percentage == other.theory_skips_percentage and
            self.practice_skips_percentage == other.practice_skips_percentage
        )


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