from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import Provider, provide, Scope

from services.telegram_bot import TelegramBotToken


class TelegramBotProvider(Provider):

    @provide(scope=Scope.APP)
    def provide_telegram_bot(
        self,
        telegram_bot_token: TelegramBotToken,
    ) -> Bot:
        return Bot(
            token=telegram_bot_token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
