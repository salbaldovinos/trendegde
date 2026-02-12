"""Cache helpers using Redis with JSON serialization."""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.core.redis import redis_client

logger = get_logger("trendedge.cache")


async def get_cached(key: str) -> Any | None:
    """Get a value from cache. Returns None on miss or error.

    Key pattern: cache:{endpoint}:{user_id}:{param_hash}
    """
    if redis_client is None:
        logger.warning("Redis not available for cache get", key=key)
        return None
    try:
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("Cache get failed", key=key, exc_info=True)
        return None


async def set_cached(key: str, value: Any, ttl: int = 60) -> None:
    """Set a value in cache with TTL (seconds).

    Key pattern: cache:{endpoint}:{user_id}:{param_hash}
    """
    if redis_client is None:
        logger.warning("Redis not available for cache set", key=key)
        return
    try:
        serialized = json.dumps(value, default=str)
        await redis_client.set(key, serialized, ex=ttl)
    except Exception:
        logger.warning("Cache set failed", key=key, exc_info=True)


async def invalidate_cache(pattern: str) -> int:
    """Delete keys matching a pattern. Returns the number of keys deleted.

    Uses SCAN to avoid blocking Redis with KEYS on large datasets.
    """
    if redis_client is None:
        logger.warning("Redis not available for cache invalidation", pattern=pattern)
        return 0
    try:
        deleted = 0
        async for key in redis_client.scan_iter(match=pattern, count=100):
            await redis_client.delete(key)
            deleted += 1
        if deleted > 0:
            logger.info("Cache invalidated", pattern=pattern, deleted_count=deleted)
        return deleted
    except Exception:
        logger.warning("Cache invalidation failed", pattern=pattern, exc_info=True)
        return 0
