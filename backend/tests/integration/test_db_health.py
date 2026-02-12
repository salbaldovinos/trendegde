"""Integration test for database connectivity via the health endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import requires_db


@requires_db
async def test_db_connectivity(async_client: AsyncClient) -> None:
    """Health/ready endpoint reports database as OK when connected."""
    resp = await async_client.get("/health/ready")
    body = resp.json()
    db_check = body.get("checks", {}).get("database", {})
    assert db_check["status"] == "ok"
    assert "latency_ms" in db_check
