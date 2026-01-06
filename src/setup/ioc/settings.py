from dishka import Provider, from_context, Scope, provide
from pydantic import PostgresDsn

from services.crypto import CryptographySecretKey
from services.telegram_bot import TelegramBotToken
from setup.settings.app import AppSettings


class SettingsProvider(Provider):
    scope = Scope.APP

    settings = from_context(AppSettings)

    @provide
    def provide_telegram_bot_token(
        self,
        settings: AppSettings,
    ) -> TelegramBotToken:
        return TelegramBotToken(settings.telegram_bot.token)

    @provide
    def provide_cryptography_secret_key(
        self,
        settings: AppSettings,
    ) -> CryptographySecretKey:
        return CryptographySecretKey(settings.cryptography.secret_key)

    @provide
    def provide_postgres_dsn(
        self,
        settings: AppSettings,
    ) -> PostgresDsn:
        return settings.database.postgres_dsn