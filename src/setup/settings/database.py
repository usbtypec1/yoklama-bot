from pydantic import BaseModel, PostgresDsn


class DatabaseSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str
    name: str

    @property
    def postgres_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.name,
            username=self.user,
        )
