"""Shared pytest fixtures for the TrendEdge test suite."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

requires_db = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set — skipping database tests",
)

requires_redis = pytest.mark.skipif(
    not os.getenv("TEST_REDIS_URL"),
    reason="TEST_REDIS_URL not set — skipping Redis tests",
)


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_database_url() -> str | None:
    """Return the test database URL, or None if not configured."""
    return os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def test_redis_url() -> str | None:
    """Return the test Redis URL, or None if not configured."""
    return os.getenv("TEST_REDIS_URL")


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator:
    """Provide an async HTTP client bound to the FastAPI test app."""
    # Import here so collection doesn't fail when deps aren't installed
    from httpx import ASGITransport, AsyncClient

    # Override settings for test environment before importing the app
    os.environ.setdefault(
        "DATABASE_URL",
        os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://trendedge:trendedge_dev@localhost:5432/trendedge_test",
        ),
    )
    os.environ.setdefault(
        "UPSTASH_REDIS_URL",
        os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1"),
    )
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
