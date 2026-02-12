"""Trendline ORM model (public.trendlines)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class Trendline(Base):
    """Detected and scored trendline (user-owned, RLS enforced)."""

    __tablename__ = "trendlines"
    __table_args__ = (
        Index("ix_trendlines_user_id", "user_id"),
        Index("ix_trendlines_instrument_id", "instrument_id"),
        Index("ix_trendlines_status", "status"),
        Index(
            "ix_trendlines_user_instrument_status",
            "user_id", "instrument_id", "status",
        ),
        CheckConstraint(
            "direction IN ('SUPPORT', 'RESISTANCE')", name="valid_direction",
        ),
        CheckConstraint(
            "status IN ('detected', 'qualifying', 'active', 'traded', "
            "'invalidated', 'expired')",
            name="valid_trendline_status",
        ),
        CheckConstraint(
            "grade IS NULL OR grade IN ('A+', 'A', 'B')", name="valid_grade",
        ),
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'detected'")
    )
    grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    anchor_pivot_1_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pivots.id", ondelete="CASCADE"),
        nullable=False,
    )
    anchor_pivot_2_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pivots.id", ondelete="CASCADE"),
        nullable=False,
    )
    slope_raw: Mapped[Decimal] = mapped_column(Numeric(16, 8), nullable=False)
    slope_degrees: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    touch_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("2")
    )
    touch_points: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    spacing_quality: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 3), nullable=True
    )
    composite_score: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    projected_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    safety_line_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    invalidation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_touch_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # created_at and updated_at inherited from Base
