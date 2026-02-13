"""RiskSettingsChangelog ORM model (public.risk_settings_changelog)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskSettingsChangelog(Base):
    """Audit trail for risk setting changes (user-owned, RLS enforced)."""

    __tablename__ = "risk_settings_changelog"
    __table_args__ = (
        Index("ix_risk_settings_changelog_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    setting_name: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # created_at and updated_at inherited from Base
