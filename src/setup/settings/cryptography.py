from pydantic import BaseModel

from services.crypto import CryptographySecretKey


class CryptographySettings(BaseModel):
    secret_key: CryptographySecretKey
