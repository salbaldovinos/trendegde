"""ContractSpecification ORM model (public.contract_specifications)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContractSpecification(Base):
    """Futures contract reference data (shared, no RLS)."""

    __tablename__ = "contract_specifications"
    __table_args__ = (
        Index("uq_contract_specifications_symbol", "symbol", unique=True),
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_class: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'futures'")
    )
    tick_size: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    tick_value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    point_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    margin_day: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    margin_overnight: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    trading_hours: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_micro: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    full_size_symbol: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # created_at and updated_at inherited from Base
