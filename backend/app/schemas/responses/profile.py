"""Pydantic response models for profile endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    """Full user profile representation."""

    id: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    timezone: str
    subscription_tier: str
    role: str
    settings: dict[str, Any]
    onboarding_completed: bool
    onboarding_step: int
    created_at: datetime
    last_login_at: datetime | None = None
