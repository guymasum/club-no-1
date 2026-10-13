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

    # SMTP for receipt emails (POST /bills/{id}/send-email). Blank smtp_host
    # means email sending is disabled — the endpoint returns a clear 500
    # instead of a confusing connection error. Provider is Gmail
    # (smtp.gmail.com) — see .env.example for the App Password requirement.
    # No vendor lock-in: swapping providers later is just an env var change.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "Club No. 1 <no-reply@clubno1.bi>"

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
