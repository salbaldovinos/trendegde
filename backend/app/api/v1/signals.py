"""Signal route handlers."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.exceptions import ConflictError, NotFoundError
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.models.signal import Signal as SignalModel
from app.db.session import get_db
from app.schemas.requests.signal_request import ManualSignalRequest
from app.schemas.responses.signal_response import (
    RiskCheckResponse,
    SignalListResponse,
    SignalResponse,
)
from app.services.signal_service import SignalService

router = APIRouter(prefix="/signals", tags=["signals"])


def _to_signal_response(data: dict) -> SignalResponse:
    """Convert service dict to SignalResponse."""
    risk_checks = None
    if data.get("risk_checks"):
        risk_checks = [
            RiskCheckResponse(
                check_name=c["check_name"],
                result=c["result"],
                actual_value=c.get("actual_value"),
                threshold_value=c.get("threshold_value"),
                details=c.get("details"),
            )
            for c in data["risk_checks"]
        ]

    return SignalResponse(
        id=data["id"],
        source=data["source"],
        status=data["status"],
        instrument_symbol=data["instrument_symbol"],
        direction=data["direction"],
        entry_type=data["entry_type"],
        entry_price=data["entry_price"],
        stop_loss_price=data.get("stop_loss_price"),
        take_profit_price=data.get("take_profit_price"),
        quantity=data.get("quantity"),
        trendline_id=data.get("trendline_id"),
        trendline_grade=data.get("trendline_grade"),
        enrichment_data=data.get("enrichment_data"),
        rejection_reason=data.get("rejection_reason"),
        risk_checks=risk_checks,
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


@router.post("/manual", response_model=SignalResponse, status_code=201)
async def create_manual_signal(
    body: ManualSignalRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SignalResponse:
    """Create a manual trading signal, run risk checks, and execute if passed."""
    svc = SignalService(db, redis)
    signal = await svc.create_manual_signal(
        uuid.UUID(user_id), body.model_dump()
    )
    data = await svc.get_signal(uuid.UUID(user_id), signal.id)
    return _to_signal_response(data)


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SignalResponse:
    """Get a signal with risk check results."""
    svc = SignalService(db, redis)
    data = await svc.get_signal(uuid.UUID(user_id), uuid.UUID(signal_id))
    return _to_signal_response(data)


@router.get("", response_model=SignalListResponse)
async def list_signals(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SignalListResponse:
    """List signals with optional status filter and pagination."""
    svc = SignalService(db, redis)
    data = await svc.list_signals(
        uuid.UUID(user_id), status_filter=status, page=page, per_page=per_page
    )
    return SignalListResponse(
        signals=[_to_signal_response(s) for s in data["signals"]],
        total=data["total"],
        page=data["page"],
        per_page=data["per_page"],
    )


_CANCELLABLE_STATUSES = {"RECEIVED", "VALIDATED", "ENRICHED", "RISK_PASSED"}


@router.patch("/{signal_id}/cancel", response_model=SignalResponse)
async def cancel_signal(
    signal_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SignalResponse:
    """Cancel a pending signal. Only signals in cancellable statuses can be cancelled."""
    stmt = select(SignalModel).where(
        SignalModel.id == uuid.UUID(signal_id),
        SignalModel.user_id == uuid.UUID(user_id),
    )
    result = await db.execute(stmt)
    signal = result.scalar_one_or_none()
    if signal is None:
        raise NotFoundError("Signal", signal_id)

    if signal.status not in _CANCELLABLE_STATUSES:
        raise ConflictError(
            f"Signal cannot be cancelled from status '{signal.status}'."
        )

    signal.status = "CANCELLED"
    await db.commit()
    await db.refresh(signal)

    svc = SignalService(db, redis)
    data = await svc.get_signal(uuid.UUID(user_id), signal.id)
    return _to_signal_response(data)
