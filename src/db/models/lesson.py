import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base


class Lesson(Base):
    __tablename__ = "lessons"

    code: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
    )

    def __repr__(self):
        return (
            f"Lesson("
            f"code={self.code}, "
            f"name={self.name}, "
            f"created_at={self.created_at})"
        )
