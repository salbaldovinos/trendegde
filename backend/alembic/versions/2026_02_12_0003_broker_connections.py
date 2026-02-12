"""Create broker_connections table with RLS policies and indexes.

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- broker_connections table --
    op.create_table(
        "broker_connections",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("broker_type", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("credentials_iv", sa.LargeBinary(), nullable=False),
        sa.Column("credentials_key_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'disconnected'"), nullable=False),
        sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("account_id", sa.Text(), nullable=True),
        sa.Column("is_paper", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_broker_connections"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_broker_connections_user_id_users",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "broker_type IN ('ibkr', 'tradovate', 'webull', 'rithmic')",
            name="ck_broker_connections_valid_broker_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'expired', 'error', 'disconnected')",
            name="ck_broker_connections_valid_status",
        ),
    )

    # -- Indexes --
    op.create_index("idx_broker_connections_user_id", "broker_connections", ["user_id"])
    op.create_index("idx_broker_connections_status", "broker_connections", ["status"])

    # -- Row-Level Security --
    op.execute(sa.text("ALTER TABLE public.broker_connections ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("ALTER TABLE public.broker_connections FORCE ROW LEVEL SECURITY;"))

    op.execute(sa.text("""
        CREATE POLICY "Users can view own broker_connections"
            ON public.broker_connections FOR SELECT
            USING (user_id = auth.uid());
    """))
    op.execute(sa.text("""
        CREATE POLICY "Users can insert own broker_connections"
            ON public.broker_connections FOR INSERT
            WITH CHECK (user_id = auth.uid());
    """))
    op.execute(sa.text("""
        CREATE POLICY "Users can update own broker_connections"
            ON public.broker_connections FOR UPDATE
            USING (user_id = auth.uid())
            WITH CHECK (user_id = auth.uid());
    """))
    op.execute(sa.text("""
        CREATE POLICY "Users can delete own broker_connections"
            ON public.broker_connections FOR DELETE
            USING (user_id = auth.uid());
    """))


def downgrade() -> None:
    # Drop RLS policies
    op.execute(sa.text(
        'DROP POLICY IF EXISTS "Users can delete own broker_connections" ON public.broker_connections;'
    ))
    op.execute(sa.text(
        'DROP POLICY IF EXISTS "Users can update own broker_connections" ON public.broker_connections;'
    ))
    op.execute(sa.text(
        'DROP POLICY IF EXISTS "Users can insert own broker_connections" ON public.broker_connections;'
    ))
    op.execute(sa.text(
        'DROP POLICY IF EXISTS "Users can view own broker_connections" ON public.broker_connections;'
    ))
    op.execute(sa.text("ALTER TABLE public.broker_connections DISABLE ROW LEVEL SECURITY;"))

    op.drop_index("idx_broker_connections_status", table_name="broker_connections")
    op.drop_index("idx_broker_connections_user_id", table_name="broker_connections")
    op.drop_table("broker_connections")
