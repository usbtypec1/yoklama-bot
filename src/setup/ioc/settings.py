from dishka import Provider, from_context, Scope, provide

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
        return CryptographySecretKey(settings.cryptography_secret.secret_key)
