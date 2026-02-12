"""User ORM model (public.users)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base


class User(Base):
    """Maps to public.users; linked to auth.users via FK."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'admin')",
            name="valid_role",
        ),
        CheckConstraint(
            "subscription_tier IN ('free', 'trader', 'pro', 'team')",
            name="valid_subscription_tier",
        ),
        Index("ix_users_deleted_at", "deleted_at"),
    )

    # Override Base.id — FK to auth.users, no server_default (comes from auth)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'user'")
    )
    subscription_tier: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'free'")
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    onboarding_step: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    settings: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # created_at and updated_at inherited from Base
