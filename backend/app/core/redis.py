"""Redis client setup and FastAPI dependency."""

from __future__ import annotations

from typing import AsyncIterator

from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("trendedge.redis")

redis_client: Redis | None = None


def init_redis() -> Redis:
    """Create and return the Redis client singleton."""
    global redis_client
    redis_client = Redis.from_url(
        settings.UPSTASH_REDIS_URL,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        max_connections=20,
    )
    logger.info("Redis client initialized", url=settings.UPSTASH_REDIS_URL[:20] + "***")
    return redis_client


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
        logger.info("Redis connection closed")


async def get_redis() -> AsyncIterator[Redis]:
    """FastAPI dependency that yields the Redis client."""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    yield redis_client
