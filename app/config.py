from dataclasses import dataclass
import os
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    database_url: str


@dataclass
class AppConfig:
    name: str
    version: str
    debug: bool


@dataclass
class Config:
    app: AppConfig
    db: DatabaseConfig
    secret_key: str
    debug: bool


def load_config(path: str = None) -> Config:
    # Загружаем переменные из .env файла
    load_dotenv(path)

    # Читаем переменные окружения с значениями по умолчанию
    return Config(
        app=AppConfig(
            name=os.getenv("APP_NAME", "My FastAPI App"),
            version=os.getenv("APP_VERSION", "1.0.0"),
            debug=os.getenv("DEBUG", "False").lower() == "true"
        ),
        db=DatabaseConfig(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./test.db")
        ),
        secret_key=os.getenv("SECRET_KEY", "default-secret-key-for-dev"),
        debug=os.getenv("DEBUG", "False").lower() == "true"
    )