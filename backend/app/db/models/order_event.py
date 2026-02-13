"""OrderEvent ORM model (public.order_events)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrderEvent(Base):
    """State transition audit trail for orders (no RLS, joined via order)."""

    __tablename__ = "order_events"
    __table_args__ = (
        Index("ix_order_events_order_id", "order_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_state: Mapped[str] = mapped_column(String(15), nullable=False)
    new_state: Mapped[str] = mapped_column(String(15), nullable=False)
    fill_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    fill_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_broker_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # created_at and updated_at inherited from Base
