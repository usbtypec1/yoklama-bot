import datetime

from sqlalchemy import func, BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    has_accepted_terms: Mapped[bool]
    student_number: Mapped[str]
    encrypted_password: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
    )

    def __repr__(self):
        return (
            f"User(id={self.id}, "
            f"has_accepted_terms={self.has_accepted_terms}, "
            f"student_number={self.student_number}, "
            f"created_at={self.created_at})"
        )
