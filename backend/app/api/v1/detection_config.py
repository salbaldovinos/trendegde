"""Detection configuration route handlers."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RateLimitError
from app.core.rate_limit import check_rate_limit
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.requests.trendline import UpdateDetectionConfigRequest
from app.schemas.responses.trendline import (
    DetectionConfigData,
    DetectionConfigResponse,
    MessageResponse,
)
from app.services.trendline_service import TrendlineService

router = APIRouter(prefix="/config", tags=["detection-config"])


# ------------------------------------------------------------------
# GET /config
# ------------------------------------------------------------------


@router.get("", response_model=DetectionConfigResponse)
async def get_config(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> DetectionConfigResponse:
    """Get the user's current detection configuration."""
    svc = TrendlineService(db, redis)
    config_dict = await svc.get_config(uuid.UUID(user_id))
    return DetectionConfigResponse(
        config=DetectionConfigData(**config_dict),
    )


# ------------------------------------------------------------------
# PUT /config
# ------------------------------------------------------------------


@router.put("", response_model=DetectionConfigResponse)
async def update_config(
    body: UpdateDetectionConfigRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> DetectionConfigResponse:
    """Update detection configuration. Triggers full recalculation."""
    # Rate limit: 10 per minute
    rl = await check_rate_limit(
        redis, f"ratelimit:user:{user_id}:config", max_requests=10, window_seconds=60
    )
    if not rl.allowed:
        raise RateLimitError(retry_after=rl.reset_at)

    data = body.model_dump(exclude_none=True)
    svc = TrendlineService(db, redis)
    config_dict = await svc.update_config(uuid.UUID(user_id), data)
    return DetectionConfigResponse(
        config=DetectionConfigData(**config_dict),
        recalculation_status="pending",
    )


# ------------------------------------------------------------------
# POST /config/reset
# ------------------------------------------------------------------


@router.post("/reset", response_model=MessageResponse)
async def reset_config(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Reset all detection parameters to defaults. Triggers recalculation."""
    # Rate limit: 10 per minute
    rl = await check_rate_limit(
        redis, f"ratelimit:user:{user_id}:config", max_requests=10, window_seconds=60
    )
    if not rl.allowed:
        raise RateLimitError(retry_after=rl.reset_at)

    svc = TrendlineService(db, redis)
    await svc.reset_config(uuid.UUID(user_id))
    return MessageResponse(
        message="Detection config reset to defaults",
        recalculation_status="pending",
    )
