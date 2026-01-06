from pydantic import BaseModel, SecretStr


class CryptographySettings(BaseModel):
    secret_key: SecretStr
