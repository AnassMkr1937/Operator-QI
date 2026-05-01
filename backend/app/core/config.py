from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    secret_key: str = Field(
        default="change-me",
        validation_alias="SECRET_KEY",
        description="JWT signing key",
    )
    algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        validation_alias="ALLOWED_ORIGINS",
    )
    https_only: bool = Field(default=False, validation_alias="HTTPS_ONLY")
    database_url: str = Field(
        default="sqlite:///./operatorqi.db",
        validation_alias="DATABASE_URL",
    )
    admin_email: str = Field(
        default="admin@operatorqi.local",
        validation_alias="ADMIN_EMAIL",
    )
    admin_password: str = Field(
        default="change-me",
        validation_alias="ADMIN_PASSWORD",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        validation_alias="RATE_LIMIT_ENABLED",
    )
    auto_create_schema: bool = Field(
        default=True,
        validation_alias="DB_AUTO_CREATE",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
