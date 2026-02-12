"""Alert ORM model (public.alerts)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class Alert(Base):
    """Trendline alert with delivery tracking (user-owned, RLS enforced)."""

    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_user_id", "user_id"),
        Index("ix_alerts_trendline_id", "trendline_id"),
        Index("ix_alerts_created_at", "created_at"),
        CheckConstraint(
            "alert_type IN ('break', 'touch', 'new_a_plus', 'invalidated')",
            name="valid_alert_type",
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    trigger_candle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candles.id", ondelete="SET NULL"),
        nullable=True,
    )
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    channels_sent: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    acknowledged: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # created_at and updated_at inherited from Base
