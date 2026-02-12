"""Role-based permission checks and tier limit enforcement."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cached, set_cached
from app.core.exceptions import ForbiddenError
from app.core.logging import get_logger
from app.core.redis import redis_client
from app.core.security import get_current_user
from app.db.session import get_db

logger = get_logger("trendedge.permissions")

# Permission cache TTL (seconds)
_PERMS_CACHE_TTL = 300  # 5 minutes

# Tier limits per resource
TIER_LIMITS: dict[str, dict[str, int]] = {
    "broker_connections": {"free": 0, "trader": 1, "pro": 3, "team": 999},
    "api_keys": {"free": 1, "trader": 5, "pro": 20, "team": 50},
    "instruments": {"free": 3, "trader": 10, "pro": 999, "team": 999},
    "playbooks": {"free": 0, "trader": 5, "pro": 999, "team": 999},
    "journal_entries_per_month": {"free": 10, "trader": 999, "pro": 999, "team": 999},
}

# Valid permissions for API keys
VALID_API_KEY_PERMISSIONS = {"webhook:write", "trades:read"}


async def get_user_permissions(
    user_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Fetch user role and tier from DB with Redis caching.

    Returns dict with 'role' and 'subscription_tier' keys.
    Cache key: perms:{user_id}, TTL 5 minutes.
    """
    cache_key = f"perms:{user_id}"

    # Try cache first
    cached = await get_cached(cache_key)
    if cached is not None:
        return cached

    # Cache miss: query DB
    from app.db.models.user import User

    result = await db.execute(
        select(User.role, User.subscription_tier).where(
            User.id == uuid.UUID(user_id),
            User.deleted_at.is_(None),
        )
    )
    row = result.one_or_none()

    if row is None:
        raise ForbiddenError("Account not found or has been deactivated.")

    perms = {"role": row.role, "subscription_tier": row.subscription_tier}

    # Populate cache
    await set_cached(cache_key, perms, ttl=_PERMS_CACHE_TTL)

    return perms


async def invalidate_permission_cache(user_id: str) -> None:
    """Delete cached permissions for a user. Call after role or tier changes."""
    if redis_client is None:
        return
    cache_key = f"perms:{user_id}"
    try:
        await redis_client.delete(cache_key)
        logger.info("Permission cache invalidated", user_id=user_id)
    except Exception:
        logger.warning("Failed to invalidate permission cache", user_id=user_id, exc_info=True)


def require_role(role: str):
    """FastAPI dependency factory that checks the user has the required role.

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role("admin"))])
    """

    async def _check_role(
        request: Request,
        user_id: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> str:
        perms = await get_user_permissions(user_id, db)
        if perms["role"] != role:
            raise ForbiddenError("You do not have permission to perform this action.")
        request.state.user_role = perms["role"]
        request.state.subscription_tier = perms["subscription_tier"]
        return user_id

    return _check_role


def require_verified_email():
    """FastAPI dependency that checks the user's email is verified via Supabase JWT claims.

    The 'email_verified' claim is set by Supabase in the JWT.
    """

    async def _check_verified(
        request: Request,
        user_id: str = Depends(get_current_user),
    ) -> str:
        # The JWT claims are available after validate_jwt runs in get_current_user.
        # Re-extract from the Authorization header to get the full claims.
        from jose import jwt as jose_jwt

        from app.core.config import settings

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split(" ", 1)[1] if " " in auth_header else ""

        claims = jose_jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )

        email_verified = claims.get("email_verified", False)
        if not email_verified:
            raise ForbiddenError("Email verification required. Please verify your email address.")

        return user_id

    return _check_verified


async def check_tier_limit(
    resource: str,
    user_id: str,
    current_count: int,
    db: AsyncSession,
) -> None:
    """Check if the user has reached their tier limit for a resource.

    Raises ForbiddenError if the limit is exceeded.
    """
    perms = await get_user_permissions(user_id, db)
    tier = perms["subscription_tier"]

    limits = TIER_LIMITS.get(resource)
    if limits is None:
        logger.warning("Unknown resource for tier limit check", resource=resource)
        return

    max_allowed = limits.get(tier, 0)

    if current_count >= max_allowed:
        # Determine next tier for upgrade message
        tier_order = ["free", "trader", "pro", "team"]
        current_idx = tier_order.index(tier) if tier in tier_order else 0
        next_tier = tier_order[current_idx + 1] if current_idx + 1 < len(tier_order) else None

        msg = f"Your {tier} plan supports up to {max_allowed} {resource.replace('_', ' ')}."
        if next_tier:
            msg += f" Upgrade to {next_tier} for more."

        raise ForbiddenError(msg)
