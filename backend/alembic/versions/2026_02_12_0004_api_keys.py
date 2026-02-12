"""Create api_keys table with RLS policies and indexes.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- api_keys table --
    op.create_table(
        "api_keys",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("key_prefix", sa.Text(), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("permissions", sa.ARRAY(sa.Text()), server_default=sa.text("'{}'::text[]"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("request_count", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_api_keys"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_api_keys_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
    )

    # -- Indexes --
    op.create_index("idx_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("idx_api_keys_is_active", "api_keys", ["is_active"])

    # -- Row-Level Security --
    op.execute(sa.text("ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("ALTER TABLE public.api_keys FORCE ROW LEVEL SECURITY;"))

    # SELECT: own rows only
    op.execute(sa.text("""
        CREATE POLICY "Users can view own api_keys"
            ON public.api_keys FOR SELECT
            USING (user_id = auth.uid());
    """))

    # INSERT: own user_id only
    op.execute(sa.text("""
        CREATE POLICY "Users can insert own api_keys"
            ON public.api_keys FOR INSERT
            WITH CHECK (user_id = auth.uid());
    """))

    # UPDATE: own rows only, cannot change user_id
    op.execute(sa.text("""
        CREATE POLICY "Users can update own api_keys"
            ON public.api_keys FOR UPDATE
            USING (user_id = auth.uid())
            WITH CHECK (user_id = auth.uid());
    """))

    # DELETE: own rows only
    op.execute(sa.text("""
        CREATE POLICY "Users can delete own api_keys"
            ON public.api_keys FOR DELETE
            USING (user_id = auth.uid());
    """))


def downgrade() -> None:
    # Drop RLS policies
    op.execute(sa.text('DROP POLICY IF EXISTS "Users can delete own api_keys" ON public.api_keys;'))
    op.execute(sa.text('DROP POLICY IF EXISTS "Users can update own api_keys" ON public.api_keys;'))
    op.execute(sa.text('DROP POLICY IF EXISTS "Users can insert own api_keys" ON public.api_keys;'))
    op.execute(sa.text('DROP POLICY IF EXISTS "Users can view own api_keys" ON public.api_keys;'))
    op.execute(sa.text("ALTER TABLE public.api_keys DISABLE ROW LEVEL SECURITY;"))

    # Drop indexes (auto-dropped with table, but explicit for clarity)
    op.drop_index("idx_api_keys_is_active", table_name="api_keys")
    op.drop_index("idx_api_keys_key_hash", table_name="api_keys")
    op.drop_index("idx_api_keys_user_id", table_name="api_keys")

    # Drop table
    op.drop_table("api_keys")
