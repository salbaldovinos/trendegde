"""UserDetectionConfig ORM model (public.user_detection_config)."""

from __future__ import annotations

import uuid
from datetime import time

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserDetectionConfig(Base):
    """Per-user trendline detection configuration (user-owned, RLS enforced)."""

    __tablename__ = "user_detection_config"
    __table_args__ = (
        CheckConstraint("min_touch_count BETWEEN 2 AND 5", name="valid_min_touch_count"),
        CheckConstraint("min_candle_spacing BETWEEN 3 AND 20", name="valid_min_candle_spacing"),
        CheckConstraint("max_slope_degrees BETWEEN 15 AND 75", name="valid_max_slope_degrees"),
        CheckConstraint("min_duration_days BETWEEN 7 AND 180", name="valid_min_duration_days"),
        CheckConstraint("touch_tolerance_atr BETWEEN 0.2 AND 1.5", name="valid_touch_tolerance"),
        CheckConstraint("pivot_n_bar_lookback BETWEEN 2 AND 10", name="valid_pivot_lookback"),
        CheckConstraint("max_lines_per_instrument BETWEEN 1 AND 10", name="valid_max_lines"),
    )

    # Use user_id as PK — no auto-generated id
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Override Base.id — this model uses user_id as PK
    id: Mapped[uuid.UUID] = mapped_column(  # type: ignore[assignment]
        UUID(as_uuid=True),
        server_default=text("gen_random_uuid()"),
        primary_key=False,
        nullable=True,
        insert_default=None,
    )
    min_touch_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("3")
    )
    min_candle_spacing: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("6")
    )
    max_slope_degrees: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("45")
    )
    min_duration_days: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("21")
    )
    touch_tolerance_atr: Mapped[float] = mapped_column(
        Numeric(3, 1), nullable=False, server_default=text("0.5")
    )
    pivot_n_bar_lookback: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("5")
    )
    max_lines_per_instrument: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("5")
    )
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_timezone: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    preset_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # created_at and updated_at inherited from Base
