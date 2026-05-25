from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "景区导览AI数字人"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/tour_guide.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen2.5-vl-7b-instruct"

    VECTOR_DB_URL: str = "http://localhost:6333"
    VECTOR_DB_COLLECTION: str = "scenic_knowledge"

    JWT_SECRET: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 52428800

    ASR_MODEL: str = "whisper-1"

    # TTS 配置
    TTS_VOICE: str = "female"
    TTS_DEVICE: str = "auto"
    TTS_LANGUAGE: str = "ZH"
    TTS_CACHE_ENABLED: bool = True
    TTS_CACHE_TTL_HOURS: int = 24

    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
