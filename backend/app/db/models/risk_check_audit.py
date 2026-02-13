"""RiskCheckAudit ORM model (public.risk_check_audit)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskCheckAudit(Base):
    """Audit trail for individual risk checks on a signal (no RLS, joined via signal)."""

    __tablename__ = "risk_check_audit"
    __table_args__ = (
        Index("ix_risk_check_audit_signal_id", "signal_id"),
        CheckConstraint(
            "result IN ('PASS', 'FAIL', 'WARN', 'SKIP')",
            name="valid_result",
        ),
    )

    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_name: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(String(4), nullable=False)
    actual_value: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    threshold_value: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    details: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # created_at and updated_at inherited from Base
