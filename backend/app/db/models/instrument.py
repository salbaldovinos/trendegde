"""Instrument ORM model (public.instruments)."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Instrument(Base):
    """Futures instrument reference data (shared, no RLS)."""

    __tablename__ = "instruments"
    __table_args__ = (
        Index("uq_instruments_symbol", "symbol", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_class: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'futures'")
    )
    tick_size: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    tick_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    contract_months: Mapped[str] = mapped_column(String(24), nullable=False)
    current_contract: Mapped[str | None] = mapped_column(String(20), nullable=True)
    roll_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    yahoo_symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata_", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # created_at and updated_at inherited from Base
