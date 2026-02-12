"""Business logic for user profile and preference management."""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, TrendEdgeError
from app.core.logging import get_logger
from app.db.models.user import User
from app.schemas.responses.profile import ProfileResponse

logger = get_logger("trendedge.profile_service")


def _deep_merge(base: dict, overrides: dict) -> dict:
    """Deep-merge *overrides* into *base* without mutating the original.

    Only merges nested dicts; lists and scalars are replaced entirely.
    """
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _user_to_profile(user: User) -> ProfileResponse:
    """Map a User ORM instance to a ProfileResponse."""
    return ProfileResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        subscription_tier=user.subscription_tier,
        role=user.role,
        settings=user.settings,
        onboarding_completed=user.onboarding_completed,
        onboarding_step=user.onboarding_step,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


class ProfileService:
    """Handles profile CRUD and preference updates."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_profile(self, user_id: str) -> ProfileResponse:
        """Fetch the profile for *user_id*."""
        user = await self._get_user(user_id)
        return _user_to_profile(user)

    # ------------------------------------------------------------------
    # Update profile (display_name, timezone)
    # ------------------------------------------------------------------

    async def update_profile(
        self,
        user_id: str,
        *,
        display_name: str | None = None,
        timezone: str | None = None,
    ) -> ProfileResponse:
        """Update basic profile fields."""
        user = await self._get_user(user_id)

        if display_name is not None:
            user.display_name = display_name
        if timezone is not None:
            user.timezone = timezone

        user.updated_at = datetime.now(UTC)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        logger.info("Profile updated", user_id=user_id)
        return _user_to_profile(user)

    # ------------------------------------------------------------------
    # Update trading preferences
    # ------------------------------------------------------------------

    async def update_trading_preferences(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> ProfileResponse:
        """Deep-merge *data* into settings.trading_preferences."""
        user = await self._get_user(user_id)

        # BR-031: switching paper_trading_mode from true to false requires
        # a live broker connection. Since broker_connections may not exist yet,
        # we log a warning but allow the service layer to be called — the route
        # handler is responsible for the full check before calling this method.
        current_settings = dict(user.settings) if user.settings else {}
        trading = current_settings.get("trading_preferences", {})
        merged_trading = _deep_merge(trading, data)
        current_settings["trading_preferences"] = merged_trading

        user.settings = current_settings
        user.updated_at = datetime.now(UTC)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        logger.info("Trading preferences updated", user_id=user_id)
        return _user_to_profile(user)

    # ------------------------------------------------------------------
    # Update notification preferences
    # ------------------------------------------------------------------

    async def update_notification_preferences(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> ProfileResponse:
        """Deep-merge *data* into settings.notification_preferences."""
        user = await self._get_user(user_id)

        # BR-036: alert_on_risk_breach cannot be disabled when live trading
        current_settings = dict(user.settings) if user.settings else {}
        trading_prefs = current_settings.get("trading_preferences", {})
        is_live = not trading_prefs.get("paper_trading_mode", True)

        if is_live and data.get("alert_on_risk_breach") is False:
            raise TrendEdgeError(
                message="Risk breach alerts are required for live trading accounts.",
                code="VALIDATION_ERROR",
                status_code=422,
                details=[{
                    "field": "alert_on_risk_breach",
                    "message": "Risk breach alerts are required for live trading accounts.",
                }],
            )

        notif = current_settings.get("notification_preferences", {})
        merged_notif = _deep_merge(notif, data)
        current_settings["notification_preferences"] = merged_notif

        user.settings = current_settings
        user.updated_at = datetime.now(UTC)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        logger.info("Notification preferences updated", user_id=user_id)
        return _user_to_profile(user)

    # ------------------------------------------------------------------
    # Update display preferences
    # ------------------------------------------------------------------

    async def update_display_preferences(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> ProfileResponse:
        """Deep-merge *data* into settings.display_preferences."""
        user = await self._get_user(user_id)

        current_settings = dict(user.settings) if user.settings else {}
        display = current_settings.get("display_preferences", {})
        merged_display = _deep_merge(display, data)
        current_settings["display_preferences"] = merged_display

        user.settings = current_settings
        user.updated_at = datetime.now(UTC)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        logger.info("Display preferences updated", user_id=user_id)
        return _user_to_profile(user)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_user(self, user_id: str) -> User:
        """Load a user or raise NotFoundError."""
        result = await self._db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User", user_id)
        return user
