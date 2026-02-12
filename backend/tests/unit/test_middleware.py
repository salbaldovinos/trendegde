"""Tests for middleware stack: request IDs, timing, and API versioning."""

from __future__ import annotations

import uuid

from httpx import AsyncClient


async def test_request_id_generated(async_client: AsyncClient) -> None:
    """Request without X-Request-ID gets a UUID assigned in the response."""
    resp = await async_client.get("/health")
    request_id = resp.headers.get("X-Request-ID")
    assert request_id is not None
    # Verify it's a valid UUID
    uuid.UUID(request_id)


async def test_request_id_preserved(async_client: AsyncClient) -> None:
    """Request with X-Request-ID preserves the same ID in the response."""
    custom_id = str(uuid.uuid4())
    resp = await async_client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp.headers.get("X-Request-ID") == custom_id


async def test_request_id_invalid_generates_new(async_client: AsyncClient) -> None:
    """Request with an invalid X-Request-ID gets a new UUID assigned."""
    resp = await async_client.get("/health", headers={"X-Request-ID": "not-a-uuid"})
    request_id = resp.headers.get("X-Request-ID")
    assert request_id is not None
    assert request_id != "not-a-uuid"
    uuid.UUID(request_id)


async def test_api_version_header(async_client: AsyncClient) -> None:
    """Every response includes the X-API-Version: v1 header."""
    resp = await async_client.get("/health")
    assert resp.headers.get("X-API-Version") == "v1"
