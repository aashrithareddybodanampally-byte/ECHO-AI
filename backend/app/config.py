import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "ECHO-AI Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql+psycopg://postgres:your_password@localhost:5432/echo_ai"
    
    # Authentication settings
    SECRET_KEY: str = "insecure-default-secret-key-do-not-use-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Audio upload settings (25 MB = 25 * 1024 * 1024 bytes)
    MAX_AUDIO_UPLOAD_BYTES: int = 25 * 1024 * 1024
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
