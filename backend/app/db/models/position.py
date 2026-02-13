"""Position ORM model (public.positions)."""

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
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class Position(Base):
    """Open or closed trade position (user-owned, RLS enforced)."""

    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_user_id_status", "user_id", "status"),
        Index("ix_positions_instrument_status", "instrument_symbol", "status"),
        CheckConstraint(
            "direction IN ('LONG', 'SHORT')",
            name="valid_position_direction",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'CLOSED')",
            name="valid_position_status",
        ),
    )

    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signals.id", ondelete="SET NULL"),
        nullable=True,
    )
    entry_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    instrument_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    stop_loss_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    take_profit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    realized_pnl: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    net_pnl: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    r_multiple: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), nullable=True
    )
    mae: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    mfe: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    mae_r: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    mfe_r: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'OPEN'")
    )
    exit_reason: Mapped[str | None] = mapped_column(String(20), nullable=True)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # created_at and updated_at inherited from Base
