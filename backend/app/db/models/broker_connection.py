"""BrokerConnection ORM model (public.broker_connections)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, LargeBinary, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class BrokerConnection(Base):
    """Encrypted broker connection with per-user ownership and health tracking."""

    __tablename__ = "broker_connections"
    __table_args__ = (
        CheckConstraint(
            "broker_type IN ('ibkr', 'tradovate', 'webull', 'rithmic')",
            name="valid_broker_type",
        ),
        CheckConstraint(
            "status IN ('active', 'expired', 'error', 'disconnected')",
            name="valid_status",
        ),
        Index("idx_broker_connections_user_id", "user_id"),
        Index("idx_broker_connections_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    broker_type: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    credentials_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    credentials_iv: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    credentials_key_id: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'disconnected'")
    )
    last_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_paper: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    # created_at and updated_at inherited from Base
