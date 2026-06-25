from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAX_FILE_SIZE: int = 20 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx"}

    class Config:
        env_file = ".env"

settings = Settings()