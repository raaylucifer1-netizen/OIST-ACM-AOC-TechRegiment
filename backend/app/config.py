"""PersonaX configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Aaru"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,https://aaruindia.vercel.app,https://frontend-qzpkbosl6-raaylucifer1-7665s-projects.vercel.app,*"

    # Database (Default to PostgreSQL, fallback to SQLite if needed)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:Upadhyay%232005@db.bpgrrhrxgowvvgwkxouz.supabase.co:5432/postgres"

    # JWT
    JWT_SECRET_KEY: str = "ef41bc789b5c328e3b5e52dc7849e3fa6cf308b2d189ef54c8e76a0d4c9d96e5"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-8b-8192"

    # Gemini
    GEMINI_API_KEY: str = "[ENCRYPTION_KEY]"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Email
    EMAIL_MODE: str = "console"  # "console" prints to terminal, "smtp" sends real emails

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
