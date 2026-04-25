from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str = "change-me"
    version: str = "0.2.0"

    # Database
    database_url: str = "sqlite:///./operatorqi_dev.db"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
