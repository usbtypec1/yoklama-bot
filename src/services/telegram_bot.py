from typing import NewType

from pydantic import SecretStr


TelegramBotToken = NewType('TelegramBotToken', SecretStr)
