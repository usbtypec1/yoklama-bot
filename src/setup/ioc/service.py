from dishka import Provider, provide, Scope

from services.crypto import PasswordCryptor
from services.obis import ObisService, ObisHttpClient, get_obis_http_client
from services.user import UserService


def service_provider() -> Provider:
    provider = Provider()
    provider.provide(
        scope=Scope.APP,
        provides=PasswordCryptor,
        source=PasswordCryptor,
    )
    provider.provide(
        scope=Scope.REQUEST,
        provides=UserService,
        source=UserService,
    )
    provider.provide(
        scope=Scope.REQUEST,
        provides=ObisService,
        source=ObisService,
    )
    provider.provide(
        scope=Scope.REQUEST,
        provides=ObisHttpClient,
        source=get_obis_http_client,
    )
    return provider
