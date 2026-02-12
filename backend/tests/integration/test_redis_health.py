"""Integration test for Redis connectivity via the health endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import requires_redis


@requires_redis
async def test_redis_connectivity(async_client: AsyncClient) -> None:
    """Health/ready endpoint reports Redis as OK when connected."""
    resp = await async_client.get("/health/ready")
    body = resp.json()
    redis_check = body.get("checks", {}).get("redis", {})
    assert redis_check["status"] == "ok"
    assert "latency_ms" in redis_check
