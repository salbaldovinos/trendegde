"""Pydantic request models for signal endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ManualSignalRequest(BaseModel):
    """Create a manual trading signal. POST /api/v1/signals/manual"""

    instrument_symbol: str = Field(min_length=1, max_length=20)
    direction: str = Field(pattern="^(LONG|SHORT)$")
    entry_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT)$")
    entry_price: float = Field(gt=0)
    stop_loss_price: float | None = Field(default=None, gt=0)
    take_profit_price: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=1, le=100)
    trendline_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("stop_loss_price")
    @classmethod
    def validate_stop(cls, v, info):
        if v is not None and "entry_price" in info.data and "direction" in info.data:
            entry = info.data["entry_price"]
            direction = info.data["direction"]
            if direction == "LONG" and v >= entry:
                raise ValueError("Stop loss must be below entry for LONG")
            if direction == "SHORT" and v <= entry:
                raise ValueError("Stop loss must be above entry for SHORT")
        return v

    @field_validator("take_profit_price")
    @classmethod
    def validate_target(cls, v, info):
        if v is not None and "entry_price" in info.data and "direction" in info.data:
            entry = info.data["entry_price"]
            direction = info.data["direction"]
            if direction == "LONG" and v <= entry:
                raise ValueError("Take profit must be above entry for LONG")
            if direction == "SHORT" and v >= entry:
                raise ValueError("Take profit must be below entry for SHORT")
        return v


class WebhookSignalPayload(BaseModel):
    """TradingView webhook payload. POST /api/v1/webhooks/tradingview/{webhook_id}"""

    ticker: str = Field(min_length=1, max_length=20)
    action: str = Field(pattern="^(buy|sell)$")  # TradingView sends lowercase
    price: float = Field(gt=0)
    stop: float | None = Field(default=None, gt=0)
    target: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=1)
    timeframe: str | None = None
    exchange: str | None = None
    message: str | None = None
