from pydantic import BaseModel

from services.telegram_bot import TelegramBotToken


class TelegramBotSettings(BaseModel):
    token: TelegramBotToken
