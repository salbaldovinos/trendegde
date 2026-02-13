"""Circuit breaker route handlers."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.responses.risk_response import CircuitBreakerStatusResponse
from app.services.risk_service import RiskService

router = APIRouter(prefix="/circuit-breaker", tags=["circuit-breaker"])


@router.get("/status", response_model=CircuitBreakerStatusResponse)
async def get_circuit_breaker_status(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CircuitBreakerStatusResponse:
    """Get current circuit breaker state."""
    svc = RiskService(db, redis)
    data = await svc.get_circuit_breaker_state(uuid.UUID(user_id))

    last_tripped = None
    if data.get("last_tripped_at"):
        raw = data["last_tripped_at"]
        last_tripped = datetime.fromisoformat(raw) if isinstance(raw, str) else raw

    return CircuitBreakerStatusResponse(
        state=data["state"],
        consecutive_losses=data["consecutive_losses"],
        threshold=data["threshold"],
        last_tripped_at=last_tripped,
        queued_signals=data["queued_signals"],
    )


@router.post("/reset", response_model=CircuitBreakerStatusResponse)
async def reset_circuit_breaker(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CircuitBreakerStatusResponse:
    """Reset the circuit breaker to CLOSED state."""
    svc = RiskService(db, redis)
    await svc.reset_circuit_breaker(uuid.UUID(user_id))
    data = await svc.get_circuit_breaker_state(uuid.UUID(user_id))

    return CircuitBreakerStatusResponse(
        state=data["state"],
        consecutive_losses=data["consecutive_losses"],
        threshold=data["threshold"],
        last_tripped_at=None,
        queued_signals=data["queued_signals"],
    )
