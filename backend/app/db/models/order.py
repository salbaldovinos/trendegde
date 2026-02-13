"""Order ORM model (public.orders)."""

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


class Order(Base):
    """Bracket order component (user-owned, RLS enforced, deletable)."""

    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_id_status", "user_id", "status"),
        Index("ix_orders_bracket_group_id", "bracket_group_id"),
        Index("ix_orders_signal_id", "signal_id"),
        CheckConstraint(
            "side IN ('BUY', 'SELL')",
            name="valid_side",
        ),
        CheckConstraint(
            "order_type IN ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT')",
            name="valid_order_type",
        ),
        CheckConstraint(
            "bracket_role IN ('ENTRY', 'STOP_LOSS', 'TAKE_PROFIT')",
            name="valid_bracket_role",
        ),
        CheckConstraint(
            "time_in_force IN ('DAY', 'GTC', 'GTD')",
            name="valid_tif",
        ),
        CheckConstraint(
            "status IN ('CONSTRUCTED', 'SUBMITTED', 'PARTIAL_FILL', "
            "'FILLED', 'CANCELLED', 'REJECTED')",
            name="valid_order_status",
        ),
    )

    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signals.id", ondelete="SET NULL"),
        nullable=True,
    )
    bracket_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    instrument_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    broker_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("broker_connections.id", ondelete="SET NULL"),
        nullable=True,
    )
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)
    bracket_role: Mapped[str] = mapped_column(String(11), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    time_in_force: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default=text("'GTC'")
    )
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, server_default=text("'CONSTRUCTED'")
    )
    broker_order_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    filled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fill_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    filled_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commission: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    slippage_ticks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # created_at and updated_at inherited from Base
