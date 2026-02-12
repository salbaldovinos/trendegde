"""Pydantic response models for broker connection endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BrokerConnectionResponse(BaseModel):
    """Single broker connection (credentials are NEVER included)."""

    id: str
    broker_type: str
    display_name: str
    status: str
    last_connected_at: datetime | None = None
    last_error: str | None = None
    account_id: str | None = None
    is_paper: bool
    created_at: datetime


class BrokerConnectionListResponse(BaseModel):
    """List of broker connections for a user."""

    connections: list[BrokerConnectionResponse]


class TestConnectionResponse(BaseModel):
    """Result of a broker connection test."""

    success: bool
    account_id: str | None = None
    balance: float | None = None
    currency: str | None = None
    error: str | None = None
