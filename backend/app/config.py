"""
Конфигурация приложения.

Загружает настройки из переменных окружения (файл .env) с помощью Pydantic Settings.
Содержит параметры для Elasticsearch, PostgreSQL, Redis и ограничений файлов.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MAX_FILE_SIZE: int = 20 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt"}

    ELASTICSEARCH_HOST: str = "elasticsearch"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX: str = "documents"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "secure_password_bpi24"
    POSTGRES_DB: str = "knowledge_base"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()