import logging
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


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

    # CORS (comma-separated origins allowed to call the API from a browser)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ML
    VOICE_EMOTION_MODEL_PATH: Path = _REPO_ROOT / "models" / "emotion_model_v1.pkl"
    STT_ENABLED: bool = True
    WHISPER_MODEL_SIZE: str = "base"

    # LLM: "auto" picks Groq if GROQ_API_KEY is set, else Anthropic if ANTHROPIC_API_KEY
    # is set, else the offline responder. Or force "groq" / "anthropic" / "offline".
    LLM_PROVIDER: str = "auto"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    ANTHROPIC_API_KEY: str | None = None
    LLM_MODEL: str = "claude-opus-5-5"  # Anthropic model
    LLM_EFFORT: str = "low"  # Anthropic only
    LLM_MAX_TOKENS: int = 2048
    LLM_TIMEOUT_SECONDS: float = 60.0

    # Context / retrieval
    CONTEXT_MAX_MESSAGES: int = 10
    CONTEXT_MAX_CHARS: int = 6000
    RAG_TOP_K: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_not_blank(cls, value: str) -> str:
        # An empty "SECRET_KEY=" line in .env would otherwise sign tokens with an empty key.
        if not value.strip():
            raise ValueError("SECRET_KEY must not be empty; set it in backend/.env")
        return value

settings = Settings()

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
