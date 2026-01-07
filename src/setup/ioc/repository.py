from dishka import Provider, Scope

from repositories.lesson import LessonRepository
from repositories.lesson_attendance import LessonAttendanceRepository
from repositories.user import UserRepository


def repository_provider() -> Provider:
    provider = Provider()
    provider.provide(
        scope=Scope.REQUEST,
        source=UserRepository,
    )
    provider.provide(
        scope=Scope.REQUEST,
        source=LessonRepository,
    )
    provider.provide(
        scope=Scope.REQUEST,
        source=LessonAttendanceRepository,
    )
    return provider
