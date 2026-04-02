"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration object.

    All values can be overridden by environment variables or a .env file.
    In production, set every secret via environment variables — never commit them.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Operator IQ"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://operatoriq:operatoriq@localhost:5432/operatoriq"

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Business rules ───────────────────────────────────────────────────────
    SKILL_DECAY_HALF_LIFE_DAYS: int = 90
    """Number of days it takes for a skill to halve in effective mastery."""

    MIN_COMPETENCY_THRESHOLD: float = 70.0
    """Minimum effective mastery score (0-100) to be considered 'qualified'."""

    MAX_REPLACEMENT_CANDIDATES: int = 10
    """Maximum number of replacement candidates returned by the matching engine."""

    TARGET_DEFECTS_PER_100: float = 2.0
    """Baseline defect rate used to compute quality penalty in matching."""

    # ── Observability ────────────────────────────────────────────────────────
    AUDIT_LOG_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings singleton. Use this in dependencies."""
    return Settings()


# Module-level singleton for direct imports (avoid repeated instantiation)
settings = get_settings()
