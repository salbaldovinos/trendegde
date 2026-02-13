"""Pydantic response models for signal endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RiskCheckResponse(BaseModel):
    check_name: str
    result: str  # PASS, FAIL, WARN, SKIP
    actual_value: float | None = None
    threshold_value: float | None = None
    details: dict[str, Any] | None = None


class SignalResponse(BaseModel):
    id: str
    source: str
    status: str
    instrument_symbol: str
    direction: str
    entry_type: str
    entry_price: float
    stop_loss_price: float | None = None
    take_profit_price: float | None = None
    quantity: int | None = None
    trendline_id: str | None = None
    trendline_grade: str | None = None
    enrichment_data: dict[str, Any] | None = None
    rejection_reason: str | None = None
    risk_checks: list[RiskCheckResponse] | None = None
    created_at: datetime
    updated_at: datetime


class SignalListResponse(BaseModel):
    signals: list[SignalResponse]
    total: int
    page: int
    per_page: int
