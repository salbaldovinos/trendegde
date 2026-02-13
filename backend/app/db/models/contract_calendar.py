"""ContractCalendar ORM model (public.contract_calendar)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContractCalendar(Base):
    """Futures contract expiration calendar (shared, no RLS)."""

    __tablename__ = "contract_calendar"
    __table_args__ = (
        UniqueConstraint(
            "instrument_family", "month_code", "year",
            name="uq_contract_calendar_family_month_year",
        ),
        Index("ix_contract_calendar_instrument_family", "instrument_family"),
    )

    instrument_family: Mapped[str] = mapped_column(String(10), nullable=False)
    contract_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    month_code: Mapped[str] = mapped_column(String(1), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    first_trade_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_trade_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rollover_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_front_month: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    # created_at and updated_at inherited from Base
