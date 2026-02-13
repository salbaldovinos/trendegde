"""Pydantic response models for order endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OrderResponse(BaseModel):
    id: str
    signal_id: str | None = None
    bracket_group_id: str
    instrument_symbol: str
    side: str
    order_type: str
    bracket_role: str
    price: float | None = None
    quantity: int
    time_in_force: str
    status: str
    broker_order_id: str | None = None
    fill_price: float | None = None
    filled_quantity: int | None = None
    commission: float | None = None
    slippage_ticks: int | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    created_at: datetime


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
    page: int
    per_page: int


class BracketGroupResponse(BaseModel):
    bracket_group_id: str
    entry: OrderResponse
    stop_loss: OrderResponse | None = None
    take_profit: OrderResponse | None = None
