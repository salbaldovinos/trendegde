"""Risk settings route handlers."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.requests.risk_settings_request import UpdateRiskSettingsRequest
from app.schemas.responses.risk_response import RiskSettingsResponse
from app.services.risk_service import RiskService

router = APIRouter(prefix="/settings", tags=["risk-settings"])


def _to_settings_response(data: dict) -> RiskSettingsResponse:
    updated_at = data["updated_at"]
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)

    return RiskSettingsResponse(
        max_position_size_micro=data["max_position_size_micro"],
        max_position_size_full=data["max_position_size_full"],
        daily_loss_limit=data["daily_loss_limit"],
        max_concurrent_positions=data["max_concurrent_positions"],
        min_risk_reward=data["min_risk_reward"],
        correlation_limit=data["correlation_limit"],
        max_single_trade_risk=data["max_single_trade_risk"],
        trading_hours_mode=data["trading_hours_mode"],
        staleness_minutes=data["staleness_minutes"],
        paper_slippage_ticks=data["paper_slippage_ticks"],
        circuit_breaker_threshold=data["circuit_breaker_threshold"],
        auto_flatten_loss_limit=data.get("auto_flatten_loss_limit"),
        is_paper_mode=data["is_paper_mode"],
        updated_at=updated_at,
    )


@router.get("/risk", response_model=RiskSettingsResponse)
async def get_risk_settings(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> RiskSettingsResponse:
    """Get current user risk settings."""
    svc = RiskService(db, redis)
    data = await svc.get_risk_settings(uuid.UUID(user_id))
    return _to_settings_response(data)


@router.put("/risk", response_model=RiskSettingsResponse)
async def update_risk_settings(
    body: UpdateRiskSettingsRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> RiskSettingsResponse:
    """Update user risk settings (partial update)."""
    svc = RiskService(db, redis)
    changes = body.model_dump(exclude_none=True)
    data = await svc.update_risk_settings(uuid.UUID(user_id), changes)
    return _to_settings_response(data)
