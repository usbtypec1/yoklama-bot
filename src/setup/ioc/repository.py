from dishka import Provider, Scope

from repositories.user import UserRepository


def repository_provider() -> Provider:
    provider = Provider()
    provider.provide(
        scope=Scope.REQUEST,
        provides=UserRepository,
        source=UserRepository,
    )
    return provider
