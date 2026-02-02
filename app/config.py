"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "ASR Middleware"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    API_KEY: str = "your-secret-api-key"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/asr_middleware"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Storage
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_STORAGE_BUCKET_NAME: str = "asr-middleware"
    AWS_S3_REGION_NAME: str = "us-east-1"
    USE_S3: bool = False
    LOCAL_STORAGE_PATH: str = "./media"
    
    # Fireflies.ai
    FIREFLIES_API_KEY: str = ""
    FIREFLIES_WEBHOOK_SECRET: str = ""
    FIREFLIES_API_URL: str = "https://api.fireflies.ai/graphql"
    
    # OpenAI (Whisper & GPT)
    OPENAI_API_KEY: str = ""
    WHISPER_MODEL: str = "large-v3"
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""
    
    # AssemblyAI
    ASSEMBLYAI_API_KEY: str = ""
    
    # Translation Services
    GOOGLE_TRANSLATE_API_KEY: str = ""
    DEEPL_API_KEY: str = ""
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
