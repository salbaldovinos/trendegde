"""Pydantic response models for risk settings and circuit breaker endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.responses.signal_response import RiskCheckResponse


class RiskSettingsResponse(BaseModel):
    max_position_size_micro: int
    max_position_size_full: int
    daily_loss_limit: float
    max_concurrent_positions: int
    min_risk_reward: float
    correlation_limit: float
    max_single_trade_risk: float
    trading_hours_mode: str
    staleness_minutes: int
    paper_slippage_ticks: int
    circuit_breaker_threshold: int
    auto_flatten_loss_limit: float | None
    is_paper_mode: bool
    updated_at: datetime


class RiskCheckAuditResponse(BaseModel):
    checks: list[RiskCheckResponse]
    signal_id: str
    overall_result: str  # PASS, FAIL


class CircuitBreakerStatusResponse(BaseModel):
    state: str  # CLOSED, TRIPPED
    consecutive_losses: int
    threshold: int
    last_tripped_at: datetime | None = None
    queued_signals: int
