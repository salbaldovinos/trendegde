"""Pydantic response models for position endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.responses.order_response import OrderResponse


class PositionResponse(BaseModel):
    id: str
    signal_id: str | None = None
    instrument_symbol: str
    direction: str
    entry_price: float
    current_price: float | None = None
    stop_loss_price: float | None = None
    take_profit_price: float | None = None
    quantity: int
    unrealized_pnl: float
    realized_pnl: float | None = None
    net_pnl: float | None = None
    r_multiple: float | None = None
    mae: float | None = None
    mfe: float | None = None
    status: str
    exit_reason: str | None = None
    entered_at: datetime
    closed_at: datetime | None = None
    created_at: datetime


class PositionListResponse(BaseModel):
    positions: list[PositionResponse]
    total: int
    page: int
    per_page: int


class ClosePositionResponse(BaseModel):
    position: PositionResponse
    closing_order: OrderResponse


class FlattenAllResponse(BaseModel):
    closed_count: int
    cancelled_orders: int
    positions: list[PositionResponse]
