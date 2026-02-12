"""Pydantic request models for broker connection endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BrokerType(str, Enum):
    ibkr = "ibkr"
    tradovate = "tradovate"
    webull = "webull"
    rithmic = "rithmic"


class BrokerStatus(str, Enum):
    active = "active"
    expired = "expired"
    error = "error"
    disconnected = "disconnected"


class CreateBrokerConnectionRequest(BaseModel):
    """Create a new broker connection."""

    broker_type: BrokerType
    display_name: str = Field(min_length=3, max_length=50)
    credentials: dict[str, Any]
    is_paper: bool = True


class UpdateBrokerConnectionRequest(BaseModel):
    """Partial update of a broker connection."""

    display_name: str | None = Field(default=None, min_length=3, max_length=50)
    credentials: dict[str, Any] | None = None
    status: BrokerStatus | None = None


class TestBrokerConnectionRequest(BaseModel):
    """Test broker credentials before saving."""

    broker_type: BrokerType
    credentials: dict[str, Any]
