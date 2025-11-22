from cryptography.fernet import Fernet


class PasswordCryptor:

    def __init__(self, secret_key: str):
        self.__fernet = Fernet(secret_key)

    def encrypt(self, plain_text: str) -> str:
        return self.__fernet.encrypt(
            plain_text.encode(encoding="utf-8"),
        ).decode(encoding="utf-8")

    def decrypt(self, cipher_text: str) -> str:
        return self.__fernet.decrypt(
            cipher_text.encode(encoding="utf-8"),
        ).decode(encoding="utf-8")
