"""Pydantic request models for profile endpoints."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Valid CME futures symbols
VALID_INSTRUMENTS = frozenset({
    "ES", "NQ", "YM", "CL", "GC", "PL", "SI", "HG", "NG",
    "ZB", "ZN", "6E", "6J", "6A", "6B", "6C", "RTY", "MES",
    "MNQ", "MYM", "MCL",
})

_DISPLAY_NAME_RE = re.compile(r"^[a-zA-Z\s\-]{2,50}$")


class ProfileUpdateRequest(BaseModel):
    """Update basic profile fields (display_name, timezone)."""

    display_name: str | None = None
    timezone: str | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters.")
        if len(v) > 50:
            raise ValueError("Name must not exceed 50 characters.")
        if not _DISPLAY_NAME_RE.match(v):
            raise ValueError("Name can only contain letters, spaces, and hyphens.")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from zoneinfo import available_timezones

        if v not in available_timezones():
            raise ValueError("Please select a valid timezone.")
        return v


class TradingPreferencesUpdateRequest(BaseModel):
    """Update trading preferences (stored in settings.trading_preferences JSONB)."""

    default_instruments: list[str] | None = None
    default_timeframe: Literal["1H", "4H", "D", "W"] | None = None
    risk_per_trade_percent: float | None = Field(default=None, ge=0.1, le=5.0)
    max_daily_loss: float | None = Field(default=None, ge=50.0, le=50000.0)
    max_concurrent_positions: int | None = Field(default=None, ge=1, le=20)
    paper_trading_mode: bool | None = None

    @field_validator("default_instruments")
    @classmethod
    def validate_instruments(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        if len(v) > 20:
            raise ValueError("You can select up to 20 default instruments.")
        for symbol in v:
            if symbol not in VALID_INSTRUMENTS:
                raise ValueError(f"Invalid instrument: {symbol}. Please select from the available instruments.")
        return v


class NotificationPreferencesUpdateRequest(BaseModel):
    """Update notification preferences (stored in settings.notification_preferences JSONB)."""

    telegram_enabled: bool | None = None
    telegram_chat_id: str | None = None
    discord_webhook_url: str | None = None
    email_digest: Literal["none", "daily", "weekly"] | None = None
    alert_on_fill: bool | None = None
    alert_on_trendline: bool | None = None
    alert_on_risk_breach: bool | None = None

    @field_validator("telegram_chat_id")
    @classmethod
    def validate_telegram_chat_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.lstrip("-").isdigit():
            raise ValueError("Chat ID must be a numeric value.")
        return v

    @field_validator("discord_webhook_url")
    @classmethod
    def validate_discord_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^https://discord\.com/api/webhooks/\d+/.+$", v):
            raise ValueError("Please enter a valid Discord webhook URL.")
        return v


class DisplayPreferencesUpdateRequest(BaseModel):
    """Update display preferences (stored in settings.display_preferences JSONB)."""

    theme: Literal["light", "dark", "system"] | None = None
    currency_display: str | None = None
    date_format: Literal["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"] | None = None
    compact_mode: bool | None = None

    @field_validator("currency_display")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Common ISO 4217 codes supported by the platform
        valid_currencies = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY"}
        if v not in valid_currencies:
            raise ValueError("Please select a valid currency.")
        return v
