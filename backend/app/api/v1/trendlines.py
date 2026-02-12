"""Trendline route handlers."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.models.instrument import Instrument
from app.db.session import get_db
from app.schemas.requests.trendline import DismissTrendlineRequest
from app.schemas.responses.trendline import (
    AnchorPoint,
    DismissResponse,
    InstrumentSummary,
    TouchPoint,
    TrendlineDetailResponse,
    TrendlineEventResponse,
    TrendlineListMeta,
    TrendlineListResponse,
    TrendlineResponse,
)
from app.services.trendline_service import TrendlineService

router = APIRouter(prefix="/trendlines", tags=["trendlines"])


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


async def _build_trendline_response(
    db: AsyncSession, tl_dict: dict
) -> TrendlineResponse:
    """Convert a service-layer trendline dict into a TrendlineResponse."""
    # Build anchor points from the pivot IDs if available, else use touch_points
    anchor_points: list[AnchorPoint] = []
    touch_points: list[TouchPoint] = []

    # Touch points from JSONB
    raw_touches = tl_dict.get("touch_points") or []
    for tp in raw_touches:
        touch_points.append(
            TouchPoint(
                timestamp=datetime.fromisoformat(tp["candle_id"])
                if "timestamp" in tp
                else datetime.min,
                price=tp.get("price", 0.0),
                candle_index=tp.get("candle_index"),
            )
        )

    return TrendlineResponse(
        id=tl_dict["id"],
        grade=tl_dict.get("grade"),
        touch_count=tl_dict["touch_count"],
        slope_degrees=tl_dict["slope_degrees"],
        duration_days=tl_dict.get("duration_days"),
        spacing_quality=tl_dict.get("spacing_quality"),
        composite_score=tl_dict.get("composite_score"),
        status=tl_dict["status"],
        direction=tl_dict["direction"],
        projected_price=tl_dict.get("projected_price"),
        safety_line_price=tl_dict.get("safety_line_price"),
        target_price=None,
        anchor_points=anchor_points,
        touch_points=touch_points,
        last_touch_at=(
            datetime.fromisoformat(tl_dict["last_touch_at"])
            if tl_dict.get("last_touch_at")
            else None
        ),
        created_at=datetime.fromisoformat(tl_dict["created_at"]),
    )


# ------------------------------------------------------------------
# GET /trendlines/{instrument_id}
# ------------------------------------------------------------------


@router.get("/{instrument_id}", response_model=TrendlineListResponse)
async def list_trendlines(
    instrument_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TrendlineListResponse:
    """List active trendlines for an instrument, split by direction."""
    instrument_uuid = uuid.UUID(instrument_id)

    # Fetch instrument for the summary
    inst_result = await db.execute(
        select(Instrument).where(Instrument.id == instrument_uuid)
    )
    instrument = inst_result.scalar_one_or_none()
    if instrument is None:
        raise NotFoundError("Instrument", instrument_id)

    svc = TrendlineService(db, redis)
    data = await svc.get_active_trendlines(uuid.UUID(user_id), instrument_uuid)

    support_lines = [
        await _build_trendline_response(db, tl) for tl in data["support"]
    ]
    resistance_lines = [
        await _build_trendline_response(db, tl) for tl in data["resistance"]
    ]

    config = await svc.get_config(uuid.UUID(user_id))

    return TrendlineListResponse(
        instrument=InstrumentSummary(
            id=str(instrument.id),
            symbol=instrument.symbol,
            name=instrument.name,
        ),
        support_lines=support_lines,
        resistance_lines=resistance_lines,
        meta=TrendlineListMeta(
            last_updated=datetime.utcnow(),
            max_lines_per_direction=config["max_lines_per_instrument"],
            support_count=len(support_lines),
            resistance_count=len(resistance_lines),
        ),
    )


# ------------------------------------------------------------------
# GET /trendlines/{trendline_id}/detail
# ------------------------------------------------------------------


@router.get("/{trendline_id}/detail", response_model=TrendlineDetailResponse)
async def get_trendline_detail(
    trendline_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TrendlineDetailResponse:
    """Get full trendline detail with touches and events."""
    svc = TrendlineService(db, redis)
    data = await svc.get_trendline_detail(uuid.UUID(user_id), uuid.UUID(trendline_id))
    if data is None:
        raise NotFoundError("Trendline", trendline_id)

    tl_response = await _build_trendline_response(db, data)

    events = [
        TrendlineEventResponse(
            id=e["id"],
            event_type=e["event_type"],
            old_value=e.get("old_value"),
            new_value=e.get("new_value"),
            reason=e.get("reason"),
            created_at=datetime.fromisoformat(e["created_at"]),
        )
        for e in data.get("events", [])
    ]

    return TrendlineDetailResponse(trendline=tl_response, events=events)


# ------------------------------------------------------------------
# PATCH /trendlines/{trendline_id}/dismiss
# ------------------------------------------------------------------


@router.patch("/{trendline_id}/dismiss", response_model=DismissResponse)
async def dismiss_trendline(
    trendline_id: str,
    body: DismissTrendlineRequest | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> DismissResponse:
    """Dismiss a trendline (transition to invalidated)."""
    reason = body.reason if body else None
    svc = TrendlineService(db, redis)
    data = await svc.dismiss_trendline(
        uuid.UUID(user_id), uuid.UUID(trendline_id), reason
    )
    return DismissResponse(
        status="invalidated",
        reason=data.get("invalidation_reason"),
    )
