"""Position route handlers."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.registry import get_adapter
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.requests.order_request import FlattenAllRequest
from app.schemas.responses.order_response import OrderResponse
from app.schemas.responses.position_response import (
    ClosePositionResponse,
    FlattenAllResponse,
    PositionListResponse,
    PositionResponse,
)
from app.services.execution_service import ExecutionService
from app.services.risk_service import RiskService

router = APIRouter(prefix="/positions", tags=["positions"])


def _to_position_response(data: dict) -> PositionResponse:
    return PositionResponse(
        id=data["id"],
        signal_id=data.get("signal_id"),
        instrument_symbol=data["instrument_symbol"],
        direction=data["direction"],
        entry_price=data["entry_price"],
        current_price=data.get("current_price"),
        stop_loss_price=data.get("stop_loss_price"),
        take_profit_price=data.get("take_profit_price"),
        quantity=data["quantity"],
        unrealized_pnl=data["unrealized_pnl"],
        realized_pnl=data.get("realized_pnl"),
        net_pnl=data.get("net_pnl"),
        r_multiple=data.get("r_multiple"),
        mae=data.get("mae"),
        mfe=data.get("mfe"),
        status=data["status"],
        exit_reason=data.get("exit_reason"),
        entered_at=datetime.fromisoformat(data["entered_at"]),
        closed_at=(
            datetime.fromisoformat(data["closed_at"])
            if data.get("closed_at")
            else None
        ),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


def _to_order_response(data: dict) -> OrderResponse:
    return OrderResponse(
        id=data["id"],
        signal_id=data.get("signal_id"),
        bracket_group_id=data["bracket_group_id"],
        instrument_symbol=data["instrument_symbol"],
        side=data["side"],
        order_type=data["order_type"],
        bracket_role=data["bracket_role"],
        price=data.get("price"),
        quantity=data["quantity"],
        time_in_force=data["time_in_force"],
        status=data["status"],
        broker_order_id=data.get("broker_order_id"),
        fill_price=data.get("fill_price"),
        filled_quantity=data.get("filled_quantity"),
        commission=data.get("commission"),
        slippage_ticks=data.get("slippage_ticks"),
        submitted_at=(
            datetime.fromisoformat(data["submitted_at"])
            if data.get("submitted_at")
            else None
        ),
        filled_at=(
            datetime.fromisoformat(data["filled_at"])
            if data.get("filled_at")
            else None
        ),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


async def _get_adapter_for_user(user_id: str, db: AsyncSession, redis: Redis):
    """Helper to get broker adapter based on user risk settings."""
    risk_svc = RiskService(db, redis)
    settings = await risk_svc.get_risk_settings(uuid.UUID(user_id))
    return await get_adapter(
        uuid.UUID(user_id), db, redis,
        is_paper=settings["is_paper_mode"],
        slippage_ticks=settings["paper_slippage_ticks"],
    )


@router.get("", response_model=PositionListResponse)
async def list_positions(
    status: str | None = Query(default=None, pattern="^(OPEN|CLOSED)$"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> PositionListResponse:
    """List positions with optional status filter."""
    svc = ExecutionService(db, redis)
    data = await svc.get_positions(
        uuid.UUID(user_id),
        status_filter=status,
        page=page,
        per_page=per_page,
    )
    return PositionListResponse(
        positions=[_to_position_response(p) for p in data["positions"]],
        total=data["total"],
        page=data["page"],
        per_page=data["per_page"],
    )


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> PositionResponse:
    """Get a single position."""
    svc = ExecutionService(db, redis)
    data = await svc.get_position(uuid.UUID(user_id), uuid.UUID(position_id))
    return _to_position_response(data)


@router.post("/{position_id}/close", response_model=ClosePositionResponse)
async def close_position(
    position_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ClosePositionResponse:
    """Close a single open position."""
    adapter = await _get_adapter_for_user(user_id, db, redis)
    svc = ExecutionService(db, redis)
    data = await svc.close_position(
        uuid.UUID(user_id), uuid.UUID(position_id), adapter
    )
    return ClosePositionResponse(
        position=_to_position_response(data["position"]),
        closing_order=_to_order_response(data["closing_order"]),
    )


@router.post("/flatten-all", response_model=FlattenAllResponse)
async def flatten_all(
    body: FlattenAllRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> FlattenAllResponse:
    """Close all open positions and cancel all pending orders."""
    adapter = await _get_adapter_for_user(user_id, db, redis)
    svc = ExecutionService(db, redis)
    data = await svc.flatten_all(uuid.UUID(user_id), adapter)
    return FlattenAllResponse(
        closed_count=data["closed_count"],
        cancelled_orders=data["cancelled_orders"],
        positions=[_to_position_response(p) for p in data["positions"]],
    )
