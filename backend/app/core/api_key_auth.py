"""API key authentication dependency for webhook endpoints."""

from __future__ import annotations

import time

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ForbiddenError, RateLimitError
from app.core.logging import get_logger
from app.core.redis import redis_client
from app.db.session import get_db
from app.services.api_key_service import validate_key

logger = get_logger("trendedge.api_key_auth")

# Rate limit: 60 requests per key per minute
_RATE_LIMIT_MAX = 60
_RATE_LIMIT_WINDOW = 60  # seconds


async def _check_api_key_rate_limit(key_hash: str) -> None:
    """Enforce per-key rate limiting using Redis sliding window.

    Key format: ratelimit:apikey:{key_hash}:{minute}
    """
    if redis_client is None:
        # Redis unavailable: degrade gracefully (no rate limiting)
        logger.warning("Redis unavailable, skipping API key rate limit check")
        return

    current_minute = int(time.time() // 60)
    rate_key = f"ratelimit:apikey:{key_hash}:{current_minute}"

    try:
        count = await redis_client.incr(rate_key)
        if count == 1:
            await redis_client.expire(rate_key, _RATE_LIMIT_WINDOW)

        if count > _RATE_LIMIT_MAX:
            logger.warning(
                "API key rate limit exceeded",
                key_hash=key_hash[:16] + "...",
                count=count,
            )
            raise RateLimitError(retry_after=_RATE_LIMIT_WINDOW)
    except RateLimitError:
        raise
    except Exception:
        logger.warning("Rate limit check failed", exc_info=True)


async def get_api_key_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str:
    """FastAPI dependency: authenticate via API key and return user_id.

    Checks X-API-Key header first, then api_key query parameter.
    Validates key, enforces rate limit, and sets RLS context.
    """
    # Extract API key from header or query param
    raw_key = request.headers.get("X-API-Key")
    if raw_key is None:
        raw_key = request.query_params.get("api_key")

    if not raw_key:
        raise AuthenticationError("API key required. Provide via X-API-Key header or api_key query parameter.")

    # Validate the key (checks active, not expired)
    api_key = await validate_key(raw_key, db)

    # Rate limit check
    await _check_api_key_rate_limit(api_key.key_hash)

    # Set request state for downstream handlers
    user_id = str(api_key.user_id)
    request.state.user_id = user_id
    request.state.api_key_id = str(api_key.id)
    request.state.api_key_permissions = api_key.permissions

    return user_id


def require_api_key_permission(permission: str):
    """FastAPI dependency factory: checks that the API key has a specific permission.

    Usage:
        @router.post("/webhooks/tradingview",
                      dependencies=[Depends(require_api_key_permission("webhook:write"))])
    """

    async def _check_permission(
        request: Request,
        user_id: str = Depends(get_api_key_user),
    ) -> str:
        permissions = getattr(request.state, "api_key_permissions", [])
        if permission not in permissions:
            raise ForbiddenError("Insufficient permissions.")
        return user_id

    return _check_permission
