"""Candle ORM model (public.candles)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class Candle(Base):
    """OHLCV candle data (shared, no RLS)."""

    __tablename__ = "candles"
    __table_args__ = (
        Index(
            "uq_candles_instrument_ts_tf",
            "instrument_id", "timestamp", "timeframe",
            unique=True,
        ),
        Index("ix_candles_instrument_id", "instrument_id"),
        Index("ix_candles_timestamp", "timestamp"),
        CheckConstraint("high >= low", name="valid_high_low"),
        CheckConstraint("volume >= 0", name="valid_volume"),
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
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'yfinance'")
    )
    atr_14: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)

    # created_at and updated_at inherited from Base
