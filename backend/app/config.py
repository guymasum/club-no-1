from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment / .env."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clubno1"
    secret_key: str = "dev-secret-change-me"
    environment: str = "development"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours, one shift

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
