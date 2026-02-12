"""Middleware stack for request processing pipeline."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

import structlog
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("trendedge.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign or propagate a unique request ID for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", "")
        try:
            uuid.UUID(request_id)
        except (ValueError, AttributeError):
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Track request duration and warn on slow requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        structlog.contextvars.bind_contextvars(duration_ms=duration_ms)

        if duration_ms > 5000:
            logger.warning(
                "Slow request: %s %s took %sms",
                request.method,
                request.url.path,
                duration_ms,
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis sorted sets."""

    EXEMPT_PATHS: set[str] = {"/health", "/health/ready", "/health/detailed"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        redis: Redis | None = getattr(request.app.state, "redis", None)
        redis_available: bool = getattr(request.app.state, "redis_available", False)

        if not redis or not redis_available:
            return await call_next(request)

        limit = settings.RATE_LIMIT_DEFAULT
        window = 60  # seconds

        # Identify client by user_id if authenticated, else by IP
        user_id = getattr(request.state, "user_id", None)
        identifier = user_id or (request.client.host if request.client else "unknown")
        key = f"ratelimit:default:{identifier}"

        now = time.time()
        window_start = now - window

        try:
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {f"{now}:{uuid.uuid4().hex[:8]}": now})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = await pipe.execute()

            current_count = results[2]
            remaining = max(0, limit - current_count)
            reset_at = int(now + window)

            if current_count > limit:
                retry_after = window
                return Response(
                    content=_rate_limit_body(
                        retry_after=retry_after,
                        request_id=getattr(request.state, "request_id", "unknown"),
                    ),
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_at),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_at)
            return response

        except Exception:
            logger.warning("Redis unavailable for rate limiting, allowing request through")
            return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request lifecycle with structured fields."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        path = request.url.path
        logger.debug("Request started: %s %s", method, path)

        response = await call_next(request)

        request_id = getattr(request.state, "request_id", "unknown")
        duration_ms = structlog.contextvars.get_contextvars().get("duration_ms")
        user_id = getattr(request.state, "user_id", None)
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")

        logger.info(
            "Request completed",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            request_id=request_id,
            ip=ip,
            user_agent=user_agent,
        )

        structlog.contextvars.unbind_contextvars("request_id", "duration_ms")

        return response


def _rate_limit_body(retry_after: int, request_id: str) -> str:
    """Build a JSON error body for 429 responses."""
    import json

    return json.dumps(
        {
            "error": {
                "code": "RATE_LIMITED",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "request_id": request_id,
                "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        }
    )
