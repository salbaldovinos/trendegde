"""Tests for health check endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def test_liveness_returns_200(async_client: AsyncClient) -> None:
    """GET /health returns 200 with status 'ok' and version."""
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "timestamp" in body


async def test_readiness_degraded_no_db(async_client: AsyncClient) -> None:
    """GET /health/ready returns 503 when the DB engine is None."""
    # The test app won't have a real DB engine, so we explicitly ensure it's None
    from app.main import app

    original = getattr(app.state, "db_engine", None)
    app.state.db_engine = None
    # Also ensure redis is unavailable so that check also degrades
    original_redis = getattr(app.state, "redis_available", False)
    app.state.redis_available = False

    try:
        resp = await async_client.get("/health/ready")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["checks"]["database"]["status"] == "error"
    finally:
        app.state.db_engine = original
        app.state.redis_available = original_redis


async def test_detailed_requires_api_key(async_client: AsyncClient) -> None:
    """GET /health/detailed without X-API-Key returns 401."""
    resp = await async_client.get("/health/detailed")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"


async def test_detailed_with_valid_key(async_client: AsyncClient) -> None:
    """GET /health/detailed with a valid operator API key returns 200."""
    from app.core.config import settings

    original = settings.OPERATOR_API_KEY
    # Temporarily set a known operator key
    object.__setattr__(settings, "OPERATOR_API_KEY", "test-operator-key-12345")
    try:
        resp = await async_client.get(
            "/health/detailed",
            headers={"X-API-Key": "test-operator-key-12345"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "version" in body
        assert "uptime_seconds" in body
    finally:
        object.__setattr__(settings, "OPERATOR_API_KEY", original)
