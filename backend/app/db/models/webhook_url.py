"""WebhookUrl ORM model (public.webhook_urls)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class WebhookUrl(Base):
    """User-owned webhook endpoint for inbound trade signals (RLS enforced, deletable)."""

    __tablename__ = "webhook_urls"
    __table_args__ = (
        Index("ix_webhook_urls_user_id", "user_id"),
        Index("uq_webhook_urls_webhook_id", "webhook_id", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    webhook_id: Mapped[str] = mapped_column(String(64), nullable=False)
    webhook_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    last_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    request_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    # created_at and updated_at inherited from Base
