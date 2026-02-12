"""TrendlineEvent ORM model (public.trendline_events)."""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TrendlineEvent(Base):
    """Audit log of trendline lifecycle events."""

    __tablename__ = "trendline_events"
    __table_args__ = (
        Index("ix_trendline_events_trendline_id", "trendline_id"),
        Index("ix_trendline_events_created_at", "created_at"),
        CheckConstraint(
            "event_type IN ('state_change', 'touch_added', 'grade_change', 'score_update')",
            name="valid_event_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    trendline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trendlines.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_candle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # created_at and updated_at inherited from Base
