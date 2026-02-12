"""UserWatchlist ORM model (public.user_watchlist)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserWatchlist(Base):
    """User-instrument subscription (user-owned, RLS enforced)."""

    __tablename__ = "user_watchlist"
    __table_args__ = (
        Index("ix_user_watchlist_user_id", "user_id"),
    )

    # Composite PK — no auto-generated id
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Override Base.id — this model uses composite PK
    id: Mapped[uuid.UUID] = mapped_column(  # type: ignore[assignment]
        UUID(as_uuid=True),
        server_default=text("gen_random_uuid()"),
        primary_key=False,
        nullable=True,
        insert_default=None,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    # created_at and updated_at inherited from Base
