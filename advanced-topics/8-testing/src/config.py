import dataclasses
import os

from flama.config import Config


@dataclasses.dataclass
class AppConfig:
    database: str
    database_user: str
    database_password: str


@dataclasses.dataclass
class DatabaseConfig:
    host: str
    port: int

    def __post_init__(self):
        self.port = int(self.port)

    def url(self, database: str, user: str, password: str) -> str:
        return (
            f"postgresql+psycopg://{user}:{password}@{self.host}:{self.port}/{database}"
        )


config = Config()

os.environ["APP_SECRET"] = (
    '{"database": "postgres","database_user": "postgres","database_password": "password"}'
)
os.environ["DATABASE_SECRET"] = '{"host": "localhost", "port": 5432}'
APP = config("APP_SECRET", cast=AppConfig)
DATABASE = config("DATABASE_SECRET", cast=DatabaseConfig)
