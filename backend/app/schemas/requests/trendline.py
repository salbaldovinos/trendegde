"""Pydantic request models for trendline detection endpoints."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class UpdateDetectionConfigRequest(BaseModel):
    """Partial update of user detection config. PUT /api/v1/config"""

    min_touch_count: int | None = Field(default=None, ge=2, le=5)
    min_candle_spacing: int | None = Field(default=None, ge=3, le=20)
    max_slope_degrees: int | None = Field(default=None, ge=15, le=75)
    min_duration_days: int | None = Field(default=None, ge=7, le=180)
    touch_tolerance_atr: float | None = Field(default=None, ge=0.2, le=1.5)
    pivot_n_bar_lookback: int | None = Field(default=None, ge=2, le=10)
    max_lines_per_instrument: int | None = Field(default=None, ge=1, le=10)
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    quiet_hours_timezone: str | None = None

    @field_validator("quiet_hours_start", "quiet_hours_end")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Must be in HH:MM format.")
        return v


class AddToWatchlistRequest(BaseModel):
    """Add instrument to user's watchlist. POST /api/v1/watchlist"""

    instrument_id: str


class DismissTrendlineRequest(BaseModel):
    """Optional reason for trendline dismissal. PATCH /api/v1/trendlines/{id}/dismiss"""

    reason: str | None = None


class SavePresetRequest(BaseModel):
    """Save current detection config as a named preset. POST /api/v1/config/presets"""

    name: str = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_preset_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9 \-]+$", v):
            raise ValueError(
                "Preset name must contain only alphanumeric characters, spaces, and hyphens."
            )
        return v
