"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # Database (required)
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    # Redis (required)
    UPSTASH_REDIS_URL: str

    # Supabase (required)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Broker APIs (optional)
    IBKR_HOST: str = ""
    IBKR_PORT: int = 4002
    TRADOVATE_API_KEY: str = ""
    TRADOVATE_API_SECRET: str = ""

    # Broker credential encryption
    BROKER_ENCRYPTION_MASTER_KEY: str = ""

    # OAuth Providers (optional)
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GITHUB_OAUTH_CLIENT_ID: str = ""
    GITHUB_OAUTH_CLIENT_SECRET: str = ""

    # Monitoring (optional)
    SENTRY_DSN: str = ""
    AXIOM_API_TOKEN: str = ""

    # Notifications (optional)
    TELEGRAM_BOT_TOKEN: str = ""

    # CORS — comma-separated string in .env, parsed into list below
    CORS_ORIGINS: str = "http://localhost:3000"

    # Rate limiting
    RATE_LIMIT_DEFAULT: int = 100

    # Operator API key for /health/detailed
    OPERATOR_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()  # type: ignore[call-arg]
