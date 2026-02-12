"""Pydantic response models for trendline detection endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

# ── Instrument models ──────────────────────────────────────────────


class InstrumentSummary(BaseModel):
    """Minimal instrument info embedded in trendline responses."""

    id: str
    symbol: str
    name: str


class InstrumentResponse(BaseModel):
    """Full instrument detail."""

    id: str
    symbol: str
    name: str
    exchange: str
    asset_class: str
    tick_size: float
    tick_value: float
    contract_months: str
    current_contract: str | None = None
    roll_date: str | None = None
    is_active: bool


class InstrumentListResponse(BaseModel):
    """List of all available instruments."""

    instruments: list[InstrumentResponse]


# ── Trendline models ──────────────────────────────────────────────


class AnchorPoint(BaseModel):
    """Start/end anchor point defining the trendline."""

    timestamp: datetime
    price: float


class TouchPoint(BaseModel):
    """A point where price touched the trendline."""

    timestamp: datetime
    price: float
    candle_index: int | None = None


class TrendlineResponse(BaseModel):
    """Single trendline with scoring and projection data."""

    id: str
    grade: str | None = None
    touch_count: int
    slope_degrees: float
    duration_days: int | None = None
    spacing_quality: float | None = None
    composite_score: float | None = None
    status: str
    direction: str
    projected_price: float | None = None
    safety_line_price: float | None = None
    target_price: float | None = None
    anchor_points: list[AnchorPoint]
    touch_points: list[TouchPoint]
    last_touch_at: datetime | None = None
    created_at: datetime


class TrendlineListMeta(BaseModel):
    """Metadata for trendline list responses."""

    last_updated: datetime | None = None
    max_lines_per_direction: int
    support_count: int
    resistance_count: int


class TrendlineListResponse(BaseModel):
    """Active trendlines for an instrument, split by direction."""

    instrument: InstrumentSummary
    support_lines: list[TrendlineResponse]
    resistance_lines: list[TrendlineResponse]
    meta: TrendlineListMeta


class TrendlineEventResponse(BaseModel):
    """Single trendline lifecycle event."""

    id: str
    event_type: str
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    reason: str | None = None
    created_at: datetime


class TrendlineDetailResponse(BaseModel):
    """Full trendline detail with event history."""

    trendline: TrendlineResponse
    events: list[TrendlineEventResponse]


# ── Detection config models ───────────────────────────────────────


class DetectionConfigData(BaseModel):
    """Detection parameter values."""

    min_touch_count: int
    min_candle_spacing: int
    max_slope_degrees: int
    min_duration_days: int
    touch_tolerance_atr: float
    pivot_n_bar_lookback: int
    max_lines_per_instrument: int
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    quiet_hours_timezone: str | None = None
    preset_name: str | None = None


class DetectionConfigResponse(BaseModel):
    """Detection config with optional recalculation status."""

    config: DetectionConfigData
    recalculation_status: str | None = None
    estimated_completion_seconds: int | None = None


class PresetResponse(BaseModel):
    """Single detection config preset."""

    name: str
    is_builtin: bool
    config: DetectionConfigData


class PresetListResponse(BaseModel):
    """List of available presets."""

    presets: list[PresetResponse]


# ── Alert models ──────────────────────────────────────────────────


class AlertResponse(BaseModel):
    """Single trendline alert."""

    id: str
    trendline_id: str
    alert_type: str
    direction: str | None = None
    payload: dict[str, Any]
    channels_sent: list[str]
    acknowledged: bool
    acknowledged_at: datetime | None = None
    created_at: datetime


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""

    alerts: list[AlertResponse]
    total: int
    page: int
    per_page: int


class AlertDetailResponse(BaseModel):
    """Single alert detail (same shape, explicit wrapper)."""

    alert: AlertResponse


# ── Watchlist models ──────────────────────────────────────────────


class WatchlistItemResponse(BaseModel):
    """Single watchlist entry with instrument info."""

    instrument: InstrumentResponse
    is_active: bool
    trendline_count: int | None = None
    created_at: datetime


class WatchlistResponse(BaseModel):
    """Full user watchlist."""

    watchlist: list[WatchlistItemResponse]


class WatchlistAddResponse(BaseModel):
    """Confirmation after adding an instrument to the watchlist."""

    instrument_id: str
    status: str
    estimated_completion_seconds: int


# ── Generic trendline responses ───────────────────────────────────


class MessageResponse(BaseModel):
    """Simple message with optional recalculation status."""

    message: str
    recalculation_status: str | None = None


class DismissResponse(BaseModel):
    """Confirmation of trendline dismissal."""

    status: str
    reason: str | None = None
