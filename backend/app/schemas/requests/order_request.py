"""Pydantic request models for order endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class OrderModificationRequest(BaseModel):
    """Modify an existing order's price or quantity. PATCH /api/v1/orders/{order_id}"""

    new_price: float | None = Field(default=None, gt=0)
    new_quantity: int | None = Field(default=None, ge=1, le=100)


class FlattenAllRequest(BaseModel):
    """Flatten all open positions. POST /api/v1/positions/flatten-all"""

    confirm: bool = Field(description="Must be true to flatten all positions")

    @field_validator("confirm")
    @classmethod
    def must_confirm(cls, v):
        if not v:
            raise ValueError("Must confirm flatten-all with confirm=true")
        return v
