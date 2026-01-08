from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class LessonGrade(Base):
    __tablename__ = 'lesson_grades'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lesson_code: Mapped[str] = mapped_column(
        ForeignKey(
            "lessons.code",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )
    exam_name: Mapped[str]
    score: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(
        server_default=func.now(),
    )

    lesson: Mapped['Lesson'] = relationship(
        'Lesson',
        back_populates='grades',
    )

    def __repr__(self) -> str:
        return (
            f"LessonGrade(id={self.id}, "
            f"lesson_code={self.lesson_code}, "
            f"user_id={self.user_id}, "
            f"exam_name={self.exam_name}, "
            f"score={self.score}, "
            f"created_at={self.created_at})"
        )
