"""Tests for application configuration (Settings class)."""

from __future__ import annotations


def test_settings_defaults() -> None:
    """Verify default values from the Settings class."""
    from app.core.config import settings

    assert settings.APP_ENV == "development"
    assert settings.APP_DEBUG is False
    assert settings.APP_VERSION == "0.1.0"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.DATABASE_POOL_SIZE == 10
    assert settings.DATABASE_MAX_OVERFLOW == 5
    assert settings.RATE_LIMIT_DEFAULT == 100
    assert settings.IBKR_PORT == 4002


def test_cors_origins_parsing() -> None:
    """Test cors_origins_list splits comma-separated CORS_ORIGINS."""
    from app.core.config import Settings

    # Single origin
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
        UPSTASH_REDIS_URL="redis://localhost:6379",
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_ANON_KEY="anon",
        SUPABASE_SERVICE_ROLE_KEY="service",
        SUPABASE_JWT_SECRET="secret",
        CORS_ORIGINS="http://localhost:3000",
    )
    assert s.cors_origins_list == ["http://localhost:3000"]

    # Multiple origins
    s2 = Settings(
        DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
        UPSTASH_REDIS_URL="redis://localhost:6379",
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_ANON_KEY="anon",
        SUPABASE_SERVICE_ROLE_KEY="service",
        SUPABASE_JWT_SECRET="secret",
        CORS_ORIGINS="http://localhost:3000, https://trendedge.app , https://staging.trendedge.app",
    )
    assert s2.cors_origins_list == [
        "http://localhost:3000",
        "https://trendedge.app",
        "https://staging.trendedge.app",
    ]

    # Empty string
    s3 = Settings(
        DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
        UPSTASH_REDIS_URL="redis://localhost:6379",
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_ANON_KEY="anon",
        SUPABASE_SERVICE_ROLE_KEY="service",
        SUPABASE_JWT_SECRET="secret",
        CORS_ORIGINS="",
    )
    assert s3.cors_origins_list == []
