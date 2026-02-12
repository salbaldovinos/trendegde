"""Pivot ORM model (public.pivots)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class Pivot(Base):
    """Detected swing point (pivot high or low)."""

    __tablename__ = "pivots"
    __table_args__ = (
        Index("ix_pivots_instrument_id", "instrument_id"),
        Index("ix_pivots_candle_id", "candle_id"),
        Index("ix_pivots_type", "type"),
        CheckConstraint("type IN ('HIGH', 'LOW')", name="valid_pivot_type"),
        CheckConstraint("n_bar_lookback BETWEEN 2 AND 10", name="valid_n_bar"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
    )
    candle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candles.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(4), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    n_bar_lookback: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # created_at and updated_at inherited from Base
