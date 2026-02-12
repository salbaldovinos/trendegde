"""Service layer for API key lifecycle management."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.core.permissions import VALID_API_KEY_PERMISSIONS, check_tier_limit
from app.db.models.api_key import ApiKey

logger = get_logger("trendedge.api_key_service")

# Key prefix constants
_LIVE_PREFIX = "te_live_"
_TEST_PREFIX = "te_test_"


def _hash_key(raw_key: str) -> str:
    """Compute SHA-256 hex digest of a raw API key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _generate_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns (full_key, key_prefix, key_hash).
    Full key format: te_live_ + 32 hex chars = 40 chars total.
    key_prefix: first 8 hex chars after the prefix.
    key_hash: SHA-256 hex digest of the full key.
    """
    hex_part = secrets.token_hex(16)  # 32 hex chars
    full_key = f"{_LIVE_PREFIX}{hex_part}"
    key_prefix = hex_part[:8]
    key_hash = _hash_key(full_key)
    return full_key, key_prefix, key_hash


async def create_key(
    user_id: str,
    name: str,
    permissions: list[str],
    expires_in_days: int | None,
    db: AsyncSession,
) -> tuple[ApiKey, str]:
    """Create a new API key for a user.

    Returns (ApiKey model, full_key_plaintext).
    The plaintext key is returned only once and never stored.
    """
    # Validate permissions
    invalid = set(permissions) - VALID_API_KEY_PERMISSIONS
    if invalid:
        raise ForbiddenError(f"Invalid permissions: {', '.join(sorted(invalid))}")

    # Check tier limit
    count_result = await db.execute(
        select(func.count()).select_from(ApiKey).where(
            ApiKey.user_id == uuid.UUID(user_id),
            ApiKey.is_active.is_(True),
        )
    )
    current_count = count_result.scalar_one()
    await check_tier_limit("api_keys", user_id, current_count, db)

    # Generate key
    full_key, key_prefix, key_hash = _generate_key()

    # Compute expiration
    expires_at = None
    if expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

    api_key = ApiKey(
        user_id=uuid.UUID(user_id),
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        permissions=permissions,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(
        "API key created",
        user_id=user_id,
        key_prefix=key_prefix,
        permissions=permissions,
    )

    return api_key, full_key


async def list_keys(user_id: str, db: AsyncSession) -> list[ApiKey]:
    """List all API keys for a user (active and revoked)."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == uuid.UUID(user_id))
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_key(user_id: str, key_id: str, db: AsyncSession) -> ApiKey:
    """Revoke an active API key (set is_active = false)."""
    api_key = await _get_user_key(user_id, key_id, db)

    if not api_key.is_active:
        raise ConflictError("API key is already revoked.")

    api_key.is_active = False
    await db.commit()
    await db.refresh(api_key)

    logger.info("API key revoked", user_id=user_id, key_prefix=api_key.key_prefix)
    return api_key


async def delete_key(user_id: str, key_id: str, db: AsyncSession) -> None:
    """Hard delete an API key. Only revoked keys can be deleted."""
    api_key = await _get_user_key(user_id, key_id, db)

    if api_key.is_active:
        raise ConflictError("Revoke the API key before deleting it.")

    await db.delete(api_key)
    await db.commit()

    logger.info("API key deleted", user_id=user_id, key_prefix=api_key.key_prefix)


async def validate_key(raw_key: str, db: AsyncSession) -> ApiKey:
    """Validate an API key string and return the associated ApiKey model.

    Checks: exists, is_active, not expired.
    Updates last_used_at and request_count on success.
    """
    key_hash = _hash_key(raw_key)

    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise AuthenticationError("Invalid API key.")

    if not api_key.is_active:
        raise AuthenticationError("API key has been revoked.")

    if api_key.expires_at is not None and api_key.expires_at < datetime.now(UTC):
        raise AuthenticationError("API key has expired.")

    # Update usage stats
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key.id)
        .values(
            last_used_at=datetime.now(UTC),
            request_count=ApiKey.request_count + 1,
        )
    )
    await db.commit()

    return api_key


async def _get_user_key(user_id: str, key_id: str, db: AsyncSession) -> ApiKey:
    """Fetch an API key owned by the given user, or raise NotFoundError."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == uuid.UUID(key_id),
            ApiKey.user_id == uuid.UUID(user_id),
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise NotFoundError("API key", key_id)
    return api_key
