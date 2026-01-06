from typing import NewType

from pydantic import SecretStr


CryptographySecretKey = NewType("CryptographySecretKey", SecretStr)
