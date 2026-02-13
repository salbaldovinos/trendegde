"""Pydantic request models for risk settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateRiskSettingsRequest(BaseModel):
    """Update user risk settings. PUT /api/v1/settings/risk"""

    max_position_size_micro: int | None = Field(default=None, ge=1, le=20)
    max_position_size_full: int | None = Field(default=None, ge=1, le=10)
    daily_loss_limit: float | None = Field(default=None, ge=50, le=50000)
    max_concurrent_positions: int | None = Field(default=None, ge=1, le=20)
    min_risk_reward: float | None = Field(default=None, ge=0, le=10)  # 0=disabled
    correlation_limit: float | None = Field(default=None, ge=0, le=1.0)
    max_single_trade_risk: float | None = Field(default=None, ge=10, le=10000)
    trading_hours_mode: str | None = Field(default=None, pattern="^(RTH|ETH|24H)$")
    staleness_minutes: int | None = Field(default=None, ge=1, le=60)
    paper_slippage_ticks: int | None = Field(default=None, ge=0, le=10)
    circuit_breaker_threshold: int | None = Field(default=None, ge=1, le=10)
    auto_flatten_loss_limit: float | None = Field(default=None, ge=0, le=100000)
    is_paper_mode: bool | None = None
