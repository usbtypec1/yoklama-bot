from pydantic import BaseModel, SecretStr


class TelegramBotSettings(BaseModel):
    token: SecretStr
