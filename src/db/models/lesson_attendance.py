import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base


class LessonAttendance(Base):
    __tablename__ = "lessons_attendance"

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
    theory_skips_percentage: Mapped[float | None]
    practice_skips_percentage: Mapped[float | None]
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
    )

    lesson: Mapped['Lesson'] = relationship(
        'Lesson',
        back_populates='attendances',
    )

    def __repr__(self):
        return (
            f"LessonAttendance(id={self.id}, "
            f"lesson_code={self.lesson_code}, "
            f"user_id={self.user_id}, "
            f"theory_skips_percentage={self.theory_skips_percentage}, "
            f"practice_skips_percentage={self.practice_skips_percentage}, "
            f"created_at={self.created_at})"
        )
