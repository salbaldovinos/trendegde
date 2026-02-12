"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.services.auth_service import AuthService


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthService:
    """Build an AuthService with injected DB and Redis sessions."""
    return AuthService(db, redis)


__all__ = [
    "get_auth_service",
    "get_current_user",
    "get_db",
    "get_redis",
]
