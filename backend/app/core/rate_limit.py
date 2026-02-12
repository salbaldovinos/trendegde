"""Sliding window rate limiter using Redis sorted sets."""

from __future__ import annotations

import time
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.logging import get_logger

logger = get_logger("trendedge.rate_limit")

# Account lock thresholds
_LOCK_TIER_1_FAILURES = 10
_LOCK_TIER_1_SECONDS = 900  # 15 minutes
_LOCK_TIER_2_FAILURES = 50
_LOCK_TIER_2_SECONDS = 3600  # 1 hour
_FAILED_LOGIN_TTL = 7200  # 2 hours


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: int
    limit: int


async def check_rate_limit(
    redis: Redis,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> RateLimitResult:
    """Check if a request is within rate limits using a sliding window.

    Key patterns:
        ratelimit:ip:{ip}:{endpoint}
        ratelimit:email:{email_hash}:{endpoint}

    Uses sorted sets: score = timestamp, member = unique timestamp string.
    All operations run in a pipeline for atomicity.
    """
    now = time.time()
    window_start = now - window_seconds
    reset_at = int(now + window_seconds)

    try:
        pipe = redis.pipeline(transaction=True)
        # Remove expired entries
        pipe.zremrangebyscore(key, "-inf", window_start)
        # Count entries in current window
        pipe.zcard(key)
        results = await pipe.execute()

        current_count: int = results[1]

        if current_count < max_requests:
            # Add new entry and set TTL
            pipe = redis.pipeline(transaction=True)
            pipe.zadd(key, {f"{now}": now})
            pipe.expire(key, window_seconds)
            await pipe.execute()

            return RateLimitResult(
                allowed=True,
                remaining=max_requests - current_count - 1,
                reset_at=reset_at,
                limit=max_requests,
            )

        return RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=reset_at,
            limit=max_requests,
        )
    except Exception:
        # Fail open: allow the request if Redis is unavailable
        logger.warning("Rate limit check failed, allowing request", key=key, exc_info=True)
        return RateLimitResult(
            allowed=True,
            remaining=max_requests,
            reset_at=reset_at,
            limit=max_requests,
        )


async def increment_failed_login(redis: Redis, email_hash: str, ip: str) -> int:
    """Increment failed login counters for email and IP. Returns the email failure count."""
    email_key = f"failed_login:{email_hash}"
    ip_key = f"failed_login_ip:{ip}"

    try:
        pipe = redis.pipeline(transaction=True)
        pipe.incr(email_key)
        pipe.expire(email_key, _FAILED_LOGIN_TTL)
        pipe.incr(ip_key)
        pipe.expire(ip_key, _FAILED_LOGIN_TTL)
        results = await pipe.execute()
        count: int = results[0]
        logger.info(
            "Failed login recorded",
            email_hash=email_hash,
            ip=ip,
            failure_count=count,
        )
        return count
    except Exception:
        logger.warning("Failed to record failed login", email_hash=email_hash, exc_info=True)
        return 0


async def reset_failed_login(redis: Redis, email_hash: str) -> None:
    """Reset failed login counter on successful login."""
    email_key = f"failed_login:{email_hash}"
    try:
        await redis.delete(email_key)
    except Exception:
        logger.warning("Failed to reset login counter", email_hash=email_hash, exc_info=True)


async def is_account_locked(redis: Redis, email_hash: str) -> tuple[bool, int]:
    """Check if an account is locked due to excessive failed logins.

    Returns:
        (locked, retry_after_seconds) - locked is True if account is locked,
        retry_after_seconds is 0 if not locked.
    """
    email_key = f"failed_login:{email_hash}"
    try:
        raw_count = await redis.get(email_key)
        if raw_count is None:
            return False, 0

        count = int(raw_count)
        ttl = await redis.ttl(email_key)
        if ttl < 0:
            ttl = 0

        if count >= _LOCK_TIER_2_FAILURES:
            # Ensure TTL covers the full lock period
            if ttl < _LOCK_TIER_2_SECONDS:
                await redis.expire(email_key, _LOCK_TIER_2_SECONDS)
                ttl = _LOCK_TIER_2_SECONDS
            return True, ttl

        if count >= _LOCK_TIER_1_FAILURES:
            if ttl < _LOCK_TIER_1_SECONDS:
                await redis.expire(email_key, _LOCK_TIER_1_SECONDS)
                ttl = _LOCK_TIER_1_SECONDS
            return True, ttl

        return False, 0
    except Exception:
        # Fail open: don't lock out users if Redis is down
        logger.warning("Account lock check failed, allowing access", email_hash=email_hash, exc_info=True)
        return False, 0
