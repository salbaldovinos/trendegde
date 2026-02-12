"""Request schemas for API key management."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    """Request body for creating a new API key."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="User-defined name for the API key (e.g., 'TradingView Alerts').",
    )
    expires_in_days: Literal[30, 60, 90] | None = Field(
        default=None,
        description="Key expiration in days. Null means never expires.",
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="List of permission strings (e.g., 'webhook:write', 'trades:read').",
    )
