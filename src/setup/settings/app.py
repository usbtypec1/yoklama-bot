import pathlib
import tomllib
from typing import Self

from pydantic import BaseModel

from setup.settings.cryptography import CryptographySettings
from setup.settings.telegram_bot import TelegramBotSettings


class AppSettings(BaseModel):
    telegram_bot: TelegramBotSettings
    cryptography: CryptographySettings

    @classmethod
    def from_settings_toml_file(cls) -> Self:
        file_path = pathlib.Path(__file__).parents[3] / "settings.toml"
        config_toml = file_path.read_text(encoding="utf-8")
        config = tomllib.loads(config_toml)
        return cls.model_validate(config)
