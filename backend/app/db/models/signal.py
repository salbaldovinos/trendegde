"""Signal ORM model (public.signals)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Signal(Base):
    """Inbound trade signal from trendline engine, webhook, or manual entry (user-owned, RLS enforced)."""

    __tablename__ = "signals"
    __table_args__ = (
        Index("ix_signals_user_id_status", "user_id", "status"),
        Index("ix_signals_instrument_status", "instrument_symbol", "status"),
        CheckConstraint(
            "source IN ('INTERNAL', 'WEBHOOK', 'MANUAL')",
            name="valid_source",
        ),
        CheckConstraint(
            "status IN ('RECEIVED', 'VALIDATED', 'ENRICHED', 'RISK_PASSED', "
            "'EXECUTING', 'FILLED', 'REJECTED', 'CANCELLED', 'EXPIRED')",
            name="valid_signal_status",
        ),
        CheckConstraint(
            "direction IN ('LONG', 'SHORT')",
            name="valid_signal_direction",
        ),
        CheckConstraint(
            "entry_type IN ('MARKET', 'LIMIT')",
            name="valid_entry_type",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'RECEIVED'")
    )
    instrument_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)
    entry_type: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'MARKET'")
    )
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    stop_loss_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    take_profit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trendline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trendlines.id", ondelete="SET NULL"),
        nullable=True,
    )
    trendline_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    webhook_url_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_urls.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    enrichment_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # created_at and updated_at inherited from Base
