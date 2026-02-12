"""Profile route handlers."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.requests.profile import (
    DisplayPreferencesUpdateRequest,
    NotificationPreferencesUpdateRequest,
    ProfileUpdateRequest,
    TradingPreferencesUpdateRequest,
)
from app.schemas.responses.profile import ProfileResponse
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


# ------------------------------------------------------------------
# GET /profile
# ------------------------------------------------------------------


@router.get("", response_model=ProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Return the authenticated user's profile."""
    svc = ProfileService(db)
    return await svc.get_profile(user_id)


# ------------------------------------------------------------------
# PATCH /profile
# ------------------------------------------------------------------


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update basic profile fields (display_name, timezone)."""
    svc = ProfileService(db)
    return await svc.update_profile(
        user_id,
        display_name=body.display_name,
        timezone=body.timezone,
    )


# ------------------------------------------------------------------
# PATCH /profile/trading
# ------------------------------------------------------------------


@router.patch("/trading", response_model=ProfileResponse)
async def update_trading_preferences(
    body: TradingPreferencesUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update trading preferences (deep merge into settings JSONB)."""
    data = body.model_dump(exclude_none=True)
    svc = ProfileService(db)
    return await svc.update_trading_preferences(user_id, data)


# ------------------------------------------------------------------
# PATCH /profile/notifications
# ------------------------------------------------------------------


@router.patch("/notifications", response_model=ProfileResponse)
async def update_notification_preferences(
    body: NotificationPreferencesUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update notification preferences (deep merge into settings JSONB)."""
    data = body.model_dump(exclude_none=True)
    svc = ProfileService(db)
    return await svc.update_notification_preferences(user_id, data)


# ------------------------------------------------------------------
# PATCH /profile/display
# ------------------------------------------------------------------


@router.patch("/display", response_model=ProfileResponse)
async def update_display_preferences(
    body: DisplayPreferencesUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update display preferences (deep merge into settings JSONB)."""
    data = body.model_dump(exclude_none=True)
    svc = ProfileService(db)
    return await svc.update_display_preferences(user_id, data)
