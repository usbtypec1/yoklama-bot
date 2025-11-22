import tomllib
import pathlib

from pydantic import BaseModel, SecretStr


class TelegramBotSettings(BaseModel):
    token: SecretStr


class CryptographySettings(BaseModel):
    secret_key: SecretStr


class AppSettings(BaseModel):
    telegram_bot: TelegramBotSettings
    cryptography: CryptographySettings


def load_settings() -> AppSettings:
    file_path = pathlib.Path(__file__).parents[1] / "settings.toml"
    settings_toml = file_path.read_text(encoding="utf-8")
    settings_dict = tomllib.loads(settings_toml)
    return AppSettings.model_validate(settings_dict)
