"""Watchlist route handlers."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.models.instrument import Instrument
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.requests.trendline import AddToWatchlistRequest
from app.schemas.responses.trendline import (
    InstrumentResponse,
    MessageResponse,
    WatchlistAddResponse,
    WatchlistItemResponse,
    WatchlistResponse,
)
from app.services.trendline_service import TrendlineService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


async def _get_user_tier(db: AsyncSession, user_id: str) -> str:
    """Helper to fetch user's subscription tier."""
    result = await db.execute(
        select(User.subscription_tier).where(User.id == user_id)
    )
    tier = result.scalar_one_or_none()
    return tier or "free"


# ------------------------------------------------------------------
# GET /watchlist
# ------------------------------------------------------------------


@router.get("", response_model=WatchlistResponse)
async def get_watchlist(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> WatchlistResponse:
    """List instruments on the user's watchlist."""
    svc = TrendlineService(db, redis)
    items = await svc.get_watchlist(uuid.UUID(user_id))

    watchlist_items: list[WatchlistItemResponse] = []
    for item in items:
        # Fetch full instrument details for each item
        inst_result = await db.execute(
            select(Instrument).where(
                Instrument.id == uuid.UUID(item["instrument_id"])
            )
        )
        inst = inst_result.scalar_one_or_none()
        if inst is None:
            continue

        watchlist_items.append(
            WatchlistItemResponse(
                instrument=InstrumentResponse(
                    id=str(inst.id),
                    symbol=inst.symbol,
                    name=inst.name,
                    exchange=inst.exchange,
                    asset_class=inst.asset_class,
                    tick_size=float(inst.tick_size),
                    tick_value=float(inst.tick_value),
                    contract_months=inst.contract_months,
                    current_contract=inst.current_contract,
                    roll_date=str(inst.roll_date) if inst.roll_date else None,
                    is_active=inst.is_active,
                ),
                is_active=item["is_active"],
                trendline_count=None,
                created_at=datetime.fromisoformat(item["added_at"]),
            )
        )

    return WatchlistResponse(watchlist=watchlist_items)


# ------------------------------------------------------------------
# POST /watchlist
# ------------------------------------------------------------------


@router.post("", response_model=WatchlistAddResponse, status_code=201)
async def add_to_watchlist(
    body: AddToWatchlistRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> WatchlistAddResponse:
    """Add an instrument to the user's watchlist."""
    tier = await _get_user_tier(db, user_id)
    svc = TrendlineService(db, redis)
    data = await svc.add_to_watchlist(
        uuid.UUID(user_id), uuid.UUID(body.instrument_id), tier
    )
    return WatchlistAddResponse(
        instrument_id=data["instrument_id"],
        status="bootstrapping",
        estimated_completion_seconds=30,
    )


# ------------------------------------------------------------------
# DELETE /watchlist/{instrument_id}
# ------------------------------------------------------------------


@router.delete("/{instrument_id}", response_model=MessageResponse)
async def remove_from_watchlist(
    instrument_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Remove an instrument from the user's watchlist (soft delete)."""
    svc = TrendlineService(db, redis)
    await svc.remove_from_watchlist(uuid.UUID(user_id), uuid.UUID(instrument_id))
    return MessageResponse(message="Instrument removed from watchlist")
