"""Order route handlers."""

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
from app.schemas.requests.order_request import OrderModificationRequest
from app.schemas.responses.order_response import OrderListResponse, OrderResponse
from app.services.execution_service import ExecutionService
from app.services.risk_service import RiskService

router = APIRouter(prefix="/orders", tags=["orders"])


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


@router.get("", response_model=OrderListResponse)
async def list_orders(
    status: str | None = Query(default=None),
    bracket_group_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OrderListResponse:
    """List orders with optional filters."""
    svc = ExecutionService(db, redis)
    data = await svc.get_orders(
        uuid.UUID(user_id),
        status_filter=status,
        bracket_group_id=bracket_group_id,
        page=page,
        per_page=per_page,
    )
    return OrderListResponse(
        orders=[_to_order_response(o) for o in data["orders"]],
        total=data["total"],
        page=data["page"],
        per_page=data["per_page"],
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OrderResponse:
    """Get a single order."""
    svc = ExecutionService(db, redis)
    data = await svc.get_order(uuid.UUID(user_id), uuid.UUID(order_id))
    return _to_order_response(data)


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OrderResponse:
    """Cancel a pending order."""
    risk_svc = RiskService(db, redis)
    settings = await risk_svc.get_risk_settings(uuid.UUID(user_id))
    adapter = await get_adapter(
        uuid.UUID(user_id), db, redis,
        is_paper=settings["is_paper_mode"],
        slippage_ticks=settings["paper_slippage_ticks"],
    )
    svc = ExecutionService(db, redis)
    data = await svc.cancel_order(uuid.UUID(user_id), uuid.UUID(order_id), adapter)
    return _to_order_response(data)


@router.patch("/{order_id}", response_model=OrderResponse)
async def modify_order(
    order_id: str,
    body: OrderModificationRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OrderResponse:
    """Modify a pending order's price or quantity."""
    risk_svc = RiskService(db, redis)
    settings = await risk_svc.get_risk_settings(uuid.UUID(user_id))
    adapter = await get_adapter(
        uuid.UUID(user_id), db, redis,
        is_paper=settings["is_paper_mode"],
        slippage_ticks=settings["paper_slippage_ticks"],
    )
    svc = ExecutionService(db, redis)
    data = await svc.modify_order(
        uuid.UUID(user_id),
        uuid.UUID(order_id),
        body.model_dump(exclude_none=True),
        adapter,
    )
    return _to_order_response(data)
