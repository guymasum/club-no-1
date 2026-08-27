from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment / .env."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clubno1"
    secret_key: str = "dev-secret-change-me"
    environment: str = "development"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours, one shift

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", mode="before")
    @classmethod
    def _use_asyncpg_driver(cls, value: str) -> str:
        """Managed Postgres (Railway, Heroku, ...) injects a plain
        postgres:// or postgresql:// DATABASE_URL. We need the asyncpg
        driver, so rewrite the scheme rather than requiring every deploy
        target to know that detail."""
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://") :]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
