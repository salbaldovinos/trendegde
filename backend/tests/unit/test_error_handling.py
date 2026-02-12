"""Tests for error handling and exception formatting."""

from __future__ import annotations

from httpx import AsyncClient


async def test_validation_error_format(async_client: AsyncClient) -> None:
    """POST to auth endpoint with invalid body returns 400 VALIDATION_ERROR."""
    resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "short"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"
    assert "request_id" in body["error"]
    assert "timestamp" in body["error"]
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) > 0


async def test_internal_error_no_stack_trace(async_client: AsyncClient) -> None:
    """Unhandled exception returns 500 with no traceback or file paths."""
    from app.main import app
    from fastapi import Request

    # Add a temporary route that raises an unhandled exception
    @app.get("/_test/raise-error")
    async def _raise_error() -> None:
        raise RuntimeError("deliberate test explosion in /foo/bar.py line 42")

    try:
        resp = await async_client.get("/_test/raise-error")
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "INTERNAL_ERROR"
        # Ensure no stack trace leakage
        response_text = resp.text
        assert "Traceback" not in response_text
        assert ".py" not in response_text
        assert "line 42" not in response_text
    finally:
        # Clean up: remove the test route
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test/raise-error"]


async def test_not_found_error(async_client: AsyncClient) -> None:
    """GET to a nonexistent route returns an appropriate error status."""
    resp = await async_client.get("/api/v1/nonexistent-route-abc123")
    assert resp.status_code in (404, 405)
