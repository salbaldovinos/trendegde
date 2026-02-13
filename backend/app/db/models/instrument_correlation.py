"""InstrumentCorrelation ORM model (public.instrument_correlations)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InstrumentCorrelation(Base):
    """Pairwise instrument correlation data (shared, no RLS)."""

    __tablename__ = "instrument_correlations"
    __table_args__ = (
        UniqueConstraint(
            "instrument_a", "instrument_b",
            name="uq_instrument_correlations_pair",
        ),
        CheckConstraint(
            "instrument_a < instrument_b",
            name="valid_pair_order",
        ),
        CheckConstraint(
            "correlation BETWEEN -1.0 AND 1.0",
            name="valid_correlation_range",
        ),
    )

    instrument_a: Mapped[str] = mapped_column(String(10), nullable=False)
    instrument_b: Mapped[str] = mapped_column(String(10), nullable=False)
    correlation: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    period_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("90")
    )

    # created_at and updated_at inherited from Base
