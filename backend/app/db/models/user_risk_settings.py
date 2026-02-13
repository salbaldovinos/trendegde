"""UserRiskSettings ORM model (public.user_risk_settings)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRiskSettings(Base):
    """Per-user risk management configuration (user-owned, RLS enforced)."""

    __tablename__ = "user_risk_settings"

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
    max_position_size_micro: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("2")
    )
    max_position_size_full: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    daily_loss_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("500.00")
    )
    max_concurrent_positions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("3")
    )
    min_risk_reward: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, server_default=text("2.0")
    )
    correlation_limit: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, server_default=text("0.70")
    )
    max_single_trade_risk: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("200.00")
    )
    trading_hours_mode: Mapped[str] = mapped_column(
        String(5), nullable=False, server_default=text("'RTH'")
    )
    staleness_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("5")
    )
    paper_slippage_ticks: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    circuit_breaker_threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("3")
    )
    auto_flatten_loss_limit: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    is_paper_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    # created_at and updated_at inherited from Base
