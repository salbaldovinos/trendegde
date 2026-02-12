"""Alert route handlers."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import get_current_user
from app.db.models.alert import Alert
from app.db.session import get_db
from app.schemas.responses.trendline import AlertListResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ------------------------------------------------------------------
# GET /alerts
# ------------------------------------------------------------------


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    alert_type: str | None = Query(default=None),
    acknowledged: bool | None = Query(default=None),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertListResponse:
    """List the user's alerts with pagination and filtering."""
    query = select(Alert).where(Alert.user_id == user_id)
    count_query = select(func.count()).select_from(Alert).where(Alert.user_id == user_id)

    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
        count_query = count_query.where(Alert.alert_type == alert_type)
    if acknowledged is not None:
        query = query.where(Alert.acknowledged == acknowledged)
        count_query = count_query.where(Alert.acknowledged == acknowledged)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Alert.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        alerts=[
            AlertResponse(
                id=str(a.id),
                trendline_id=str(a.trendline_id),
                alert_type=a.alert_type,
                direction=a.direction,
                payload=a.payload,
                channels_sent=a.channels_sent,
                acknowledged=a.acknowledged,
                acknowledged_at=a.acknowledged_at,
                created_at=a.created_at,
            )
            for a in alerts
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


# ------------------------------------------------------------------
# GET /alerts/{alert_id}
# ------------------------------------------------------------------


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Get a single alert's details."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alert", alert_id)
    if str(alert.user_id) != user_id:
        raise ForbiddenError()
    return AlertResponse(
        id=str(alert.id),
        trendline_id=str(alert.trendline_id),
        alert_type=alert.alert_type,
        direction=alert.direction,
        payload=alert.payload,
        channels_sent=alert.channels_sent,
        acknowledged=alert.acknowledged,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )


# ------------------------------------------------------------------
# PATCH /alerts/{alert_id}/acknowledge
# ------------------------------------------------------------------


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Acknowledge an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alert", alert_id)
    if str(alert.user_id) != user_id:
        raise ForbiddenError()

    await db.execute(
        update(Alert)
        .where(Alert.id == alert_id)
        .values(acknowledged=True, acknowledged_at=datetime.now(UTC))
    )
    await db.commit()
    await db.refresh(alert)

    return AlertResponse(
        id=str(alert.id),
        trendline_id=str(alert.trendline_id),
        alert_type=alert.alert_type,
        direction=alert.direction,
        payload=alert.payload,
        channels_sent=alert.channels_sent,
        acknowledged=alert.acknowledged,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )
