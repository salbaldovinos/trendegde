"""Initial schema: users and audit_logs tables with RLS and triggers.

Revision ID: 0001
Revises: None
Create Date: 2026-02-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default settings JSONB for new users
DEFAULT_USER_SETTINGS = """{
  "trading_preferences": {
    "default_instruments": [],
    "default_timeframe": "4H",
    "risk_per_trade_percent": 1.0,
    "max_daily_loss": 500.00,
    "max_concurrent_positions": 3,
    "paper_trading_mode": true
  },
  "notification_preferences": {
    "telegram_enabled": false,
    "email_digest": "daily",
    "alert_on_fill": true,
    "alert_on_trendline": true,
    "alert_on_risk_breach": true
  },
  "display_preferences": {
    "theme": "system",
    "currency_display": "USD",
    "date_format": "MM/DD/YYYY",
    "compact_mode": false
  }
}"""


def upgrade() -> None:
    # -- Stub auth schema for local development (no-op on Supabase) --
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = 'auth'
            ) THEN
                CREATE SCHEMA auth;
                CREATE OR REPLACE FUNCTION auth.uid()
                RETURNS uuid
                LANGUAGE sql
                STABLE
                AS 'SELECT COALESCE(
                    current_setting(''request.jwt.claim.sub'', true)::uuid,
                    ''00000000-0000-0000-0000-000000000000''::uuid
                )';
            END IF;
        END;
        $$;
    """))

    # -- users table --
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), server_default=sa.text("'user'"), nullable=False),
        sa.Column("subscription_tier", sa.Text(), server_default=sa.text("'free'"), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("onboarding_step", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("settings", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_valid_role"),
        sa.CheckConstraint(
            "subscription_tier IN ('free', 'trader', 'pro', 'team')",
            name="ck_users_valid_subscription_tier",
        ),
    )
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    # -- audit_logs table --
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("event_data", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_audit_logs_user_id_users", ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # -- handle_new_user() trigger function --
    # Creates a public.users row when a new auth.users row is inserted
    op.execute(sa.text(f"""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
            INSERT INTO public.users (id, email, settings)
            VALUES (
                NEW.id,
                NEW.email,
                '{DEFAULT_USER_SETTINGS}'::jsonb
            );
            RETURN NEW;
        END;
        $$;
    """))

    # -- Trigger on auth.users (wrapped in DO block to handle missing auth schema) --
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'auth' AND table_name = 'users'
            ) THEN
                CREATE TRIGGER on_auth_user_created
                    AFTER INSERT ON auth.users
                    FOR EACH ROW
                    EXECUTE FUNCTION public.handle_new_user();
            END IF;
        END;
        $$;
    """))

    # -- Row-Level Security on users --
    op.execute(sa.text("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY users_select_own ON public.users
            FOR SELECT USING (auth.uid() = id);
    """))
    op.execute(sa.text("""
        CREATE POLICY users_update_own ON public.users
            FOR UPDATE USING (auth.uid() = id);
    """))

    # -- Row-Level Security on audit_logs --
    op.execute(sa.text("ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY audit_logs_select_own ON public.audit_logs
            FOR SELECT USING (auth.uid() = user_id);
    """))


def downgrade() -> None:
    # Drop RLS policies
    op.execute(sa.text("DROP POLICY IF EXISTS audit_logs_select_own ON public.audit_logs;"))
    op.execute(sa.text("ALTER TABLE public.audit_logs DISABLE ROW LEVEL SECURITY;"))

    op.execute(sa.text("DROP POLICY IF EXISTS users_update_own ON public.users;"))
    op.execute(sa.text("DROP POLICY IF EXISTS users_select_own ON public.users;"))
    op.execute(sa.text("ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;"))

    # Drop trigger (if auth schema exists)
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'auth' AND table_name = 'users'
            ) THEN
                DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
            END IF;
        END;
        $$;
    """))

    # Drop function
    op.execute(sa.text("DROP FUNCTION IF EXISTS public.handle_new_user();"))

    # Drop tables
    op.drop_table("audit_logs")
    op.drop_table("users")

    # Drop local auth stub if it was created by this migration
    # On Supabase, auth schema is managed externally so we only drop our stub function
    op.execute(sa.text("""
        DO $$
        BEGIN
            -- Only drop if this is the stub (no auth.users table means it's our stub)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'auth' AND table_name = 'users'
            ) THEN
                DROP FUNCTION IF EXISTS auth.uid();
                DROP SCHEMA IF EXISTS auth;
            END IF;
        END;
        $$;
    """))
