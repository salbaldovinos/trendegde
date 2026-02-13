"""Execution pipeline tables: contract_specifications, contract_calendar,
instrument_correlations, signals, webhook_urls, user_risk_settings,
risk_check_audit, risk_settings_changelog, orders, order_events, positions.

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- contract_specifications table (shared reference, no RLS) --
    op.create_table(
        "contract_specifications",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("exchange", sa.String(20), nullable=False),
        sa.Column("asset_class", sa.String(20), nullable=False, server_default=sa.text("'futures'")),
        sa.Column("tick_size", sa.Numeric(10, 4), nullable=False),
        sa.Column("tick_value", sa.Numeric(10, 4), nullable=False),
        sa.Column("point_value", sa.Numeric(12, 4), nullable=False),
        sa.Column("margin_day", sa.Numeric(12, 2), nullable=True),
        sa.Column("margin_overnight", sa.Numeric(12, 2), nullable=True),
        sa.Column("trading_hours", sa.String(50), nullable=True),
        sa.Column("is_micro", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("full_size_symbol", sa.String(20), nullable=True),
        sa.Column("metadata_", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_contract_specifications"),
    )
    op.create_index("uq_contract_specifications_symbol", "contract_specifications", ["symbol"], unique=True)

    # -- contract_calendar table (shared reference, no RLS) --
    op.create_table(
        "contract_calendar",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("instrument_family", sa.String(10), nullable=False),
        sa.Column("contract_symbol", sa.String(20), nullable=False),
        sa.Column("month_code", sa.String(1), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("first_trade_date", sa.Date(), nullable=True),
        sa.Column("last_trade_date", sa.Date(), nullable=True),
        sa.Column("rollover_date", sa.Date(), nullable=True),
        sa.Column("is_front_month", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_contract_calendar"),
        sa.UniqueConstraint("instrument_family", "month_code", "year", name="uq_contract_calendar_family_month_year"),
    )
    op.create_index("ix_contract_calendar_instrument_family", "contract_calendar", ["instrument_family"])

    # -- instrument_correlations table (shared reference, no RLS) --
    op.create_table(
        "instrument_correlations",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("instrument_a", sa.String(10), nullable=False),
        sa.Column("instrument_b", sa.String(10), nullable=False),
        sa.Column("correlation", sa.Numeric(5, 4), nullable=False),
        sa.Column("period_days", sa.Integer(), nullable=False, server_default=sa.text("90")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_instrument_correlations"),
        sa.UniqueConstraint("instrument_a", "instrument_b", name="uq_instrument_correlations_pair"),
        sa.CheckConstraint("instrument_a < instrument_b", name="valid_pair_order"),
        sa.CheckConstraint("correlation BETWEEN -1.0 AND 1.0", name="valid_correlation_range"),
    )

    # -- webhook_urls table (user-owned, RLS + DELETE) --
    op.create_table(
        "webhook_urls",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("webhook_id", sa.String(64), nullable=False),
        sa.Column("webhook_secret", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_webhook_urls"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_webhook_urls_user_id_users", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_webhook_urls_user_id", "webhook_urls", ["user_id"])
    op.create_index("uq_webhook_urls_webhook_id", "webhook_urls", ["webhook_id"], unique=True)

    # -- signals table (user-owned, RLS) --
    op.create_table(
        "signals",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'RECEIVED'")),
        sa.Column("instrument_symbol", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(5), nullable=False),
        sa.Column("entry_type", sa.String(10), nullable=False, server_default=sa.text("'MARKET'")),
        sa.Column("entry_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("stop_loss_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("take_profit_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("trendline_id", UUID(as_uuid=True), nullable=True),
        sa.Column("trendline_grade", sa.String(2), nullable=True),
        sa.Column("webhook_url_id", UUID(as_uuid=True), nullable=True),
        sa.Column("source_metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("enrichment_data", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_signals"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_signals_user_id_users", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trendline_id"], ["trendlines.id"],
            name="fk_signals_trendline_id_trendlines", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["webhook_url_id"], ["webhook_urls.id"],
            name="fk_signals_webhook_url_id_webhook_urls", ondelete="SET NULL",
        ),
        sa.CheckConstraint("source IN ('INTERNAL', 'WEBHOOK', 'MANUAL')", name="valid_source"),
        sa.CheckConstraint(
            "status IN ('RECEIVED', 'VALIDATED', 'ENRICHED', 'RISK_PASSED', "
            "'EXECUTING', 'FILLED', 'REJECTED', 'CANCELLED', 'EXPIRED')",
            name="valid_signal_status",
        ),
        sa.CheckConstraint("direction IN ('LONG', 'SHORT')", name="valid_signal_direction"),
        sa.CheckConstraint("entry_type IN ('MARKET', 'LIMIT')", name="valid_entry_type"),
    )
    op.create_index("ix_signals_user_id_status", "signals", ["user_id", "status"])
    op.create_index("ix_signals_instrument_status", "signals", ["instrument_symbol", "status"])

    # -- user_risk_settings table (user-owned, RLS, user_id is PK) --
    op.create_table(
        "user_risk_settings",
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("max_position_size_micro", sa.Integer(), nullable=False, server_default=sa.text("2")),
        sa.Column("max_position_size_full", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("daily_loss_limit", sa.Numeric(12, 2), nullable=False, server_default=sa.text("500.00")),
        sa.Column("max_concurrent_positions", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("min_risk_reward", sa.Numeric(4, 2), nullable=False, server_default=sa.text("2.0")),
        sa.Column("correlation_limit", sa.Numeric(3, 2), nullable=False, server_default=sa.text("0.70")),
        sa.Column("max_single_trade_risk", sa.Numeric(12, 2), nullable=False, server_default=sa.text("200.00")),
        sa.Column("trading_hours_mode", sa.String(5), nullable=False, server_default=sa.text("'RTH'")),
        sa.Column("staleness_minutes", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("paper_slippage_ticks", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("circuit_breaker_threshold", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("auto_flatten_loss_limit", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_paper_mode", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_user_risk_settings"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_user_risk_settings_user_id_users", ondelete="CASCADE",
        ),
    )

    # -- risk_check_audit table (no RLS — joined via signal→user) --
    op.create_table(
        "risk_check_audit",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("signal_id", UUID(as_uuid=True), nullable=False),
        sa.Column("check_name", sa.String(50), nullable=False),
        sa.Column("result", sa.String(4), nullable=False),
        sa.Column("actual_value", sa.Numeric(14, 4), nullable=True),
        sa.Column("threshold_value", sa.Numeric(14, 4), nullable=True),
        sa.Column("details", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_risk_check_audit"),
        sa.ForeignKeyConstraint(
            ["signal_id"], ["signals.id"],
            name="fk_risk_check_audit_signal_id_signals", ondelete="CASCADE",
        ),
        sa.CheckConstraint("result IN ('PASS', 'FAIL', 'WARN', 'SKIP')", name="valid_result"),
    )
    op.create_index("ix_risk_check_audit_signal_id", "risk_check_audit", ["signal_id"])

    # -- risk_settings_changelog table (user-owned, RLS) --
    op.create_table(
        "risk_settings_changelog",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("setting_name", sa.String(50), nullable=False),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_risk_settings_changelog"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_risk_settings_changelog_user_id_users", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_risk_settings_changelog_user_created", "risk_settings_changelog", ["user_id", "created_at"])

    # -- orders table (user-owned, RLS + DELETE) --
    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("signal_id", UUID(as_uuid=True), nullable=True),
        sa.Column("bracket_group_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_symbol", sa.String(20), nullable=False),
        sa.Column("broker_connection_id", UUID(as_uuid=True), nullable=True),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("order_type", sa.String(10), nullable=False),
        sa.Column("bracket_role", sa.String(11), nullable=False),
        sa.Column("price", sa.Numeric(12, 4), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("time_in_force", sa.String(3), nullable=False, server_default=sa.text("'GTC'")),
        sa.Column("status", sa.String(15), nullable=False, server_default=sa.text("'CONSTRUCTED'")),
        sa.Column("broker_order_id", sa.String(100), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fill_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("filled_quantity", sa.Integer(), nullable=True),
        sa.Column("commission", sa.Numeric(8, 2), nullable=True),
        sa.Column("slippage_ticks", sa.Integer(), nullable=True),
        sa.Column("metadata_", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
        sa.ForeignKeyConstraint(
            ["signal_id"], ["signals.id"],
            name="fk_orders_signal_id_signals", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_orders_user_id_users", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["broker_connection_id"], ["broker_connections.id"],
            name="fk_orders_broker_connection_id_broker_connections", ondelete="SET NULL",
        ),
        sa.CheckConstraint("side IN ('BUY', 'SELL')", name="valid_side"),
        sa.CheckConstraint("order_type IN ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT')", name="valid_order_type"),
        sa.CheckConstraint("bracket_role IN ('ENTRY', 'STOP_LOSS', 'TAKE_PROFIT')", name="valid_bracket_role"),
        sa.CheckConstraint("time_in_force IN ('DAY', 'GTC', 'GTD')", name="valid_tif"),
        sa.CheckConstraint(
            "status IN ('CONSTRUCTED', 'SUBMITTED', 'PARTIAL_FILL', 'FILLED', 'CANCELLED', 'REJECTED')",
            name="valid_order_status",
        ),
    )
    op.create_index("ix_orders_user_id_status", "orders", ["user_id", "status"])
    op.create_index("ix_orders_bracket_group_id", "orders", ["bracket_group_id"])
    op.create_index("ix_orders_signal_id", "orders", ["signal_id"])

    # -- order_events table (no RLS — joined via order→user) --
    op.create_table(
        "order_events",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("previous_state", sa.String(15), nullable=False),
        sa.Column("new_state", sa.String(15), nullable=False),
        sa.Column("fill_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("fill_quantity", sa.Integer(), nullable=True),
        sa.Column("raw_broker_response", JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_order_events"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"],
            name="fk_order_events_order_id_orders", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_order_events_order_id", "order_events", ["order_id"])

    # -- positions table (user-owned, RLS) --
    op.create_table(
        "positions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("signal_id", UUID(as_uuid=True), nullable=True),
        sa.Column("entry_order_id", UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_symbol", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(5), nullable=False),
        sa.Column("entry_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("current_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("stop_loss_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("take_profit_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("realized_pnl", sa.Numeric(14, 2), nullable=True),
        sa.Column("net_pnl", sa.Numeric(14, 2), nullable=True),
        sa.Column("r_multiple", sa.Numeric(8, 4), nullable=True),
        sa.Column("mae", sa.Numeric(12, 4), nullable=True),
        sa.Column("mfe", sa.Numeric(12, 4), nullable=True),
        sa.Column("mae_r", sa.Numeric(8, 4), nullable=True),
        sa.Column("mfe_r", sa.Numeric(8, 4), nullable=True),
        sa.Column("status", sa.String(10), nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("exit_reason", sa.String(20), nullable=True),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_positions"),
        sa.ForeignKeyConstraint(
            ["signal_id"], ["signals.id"],
            name="fk_positions_signal_id_signals", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["entry_order_id"], ["orders.id"],
            name="fk_positions_entry_order_id_orders", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_positions_user_id_users", ondelete="CASCADE",
        ),
        sa.CheckConstraint("direction IN ('LONG', 'SHORT')", name="valid_position_direction"),
        sa.CheckConstraint("status IN ('OPEN', 'CLOSED')", name="valid_position_status"),
    )
    op.create_index("ix_positions_user_id_status", "positions", ["user_id", "status"])
    op.create_index("ix_positions_instrument_status", "positions", ["instrument_symbol", "status"])

    # ================================================================
    # Row-Level Security policies
    # ================================================================

    # -- RLS: webhook_urls (SELECT, INSERT, UPDATE, DELETE) --
    op.execute(sa.text("ALTER TABLE public.webhook_urls ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY webhook_urls_select_own ON public.webhook_urls
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY webhook_urls_insert_own ON public.webhook_urls
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY webhook_urls_update_own ON public.webhook_urls
            FOR UPDATE USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY webhook_urls_delete_own ON public.webhook_urls
            FOR DELETE USING (auth.uid() = user_id);
    """))

    # -- RLS: signals (SELECT, INSERT, UPDATE) --
    op.execute(sa.text("ALTER TABLE public.signals ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY signals_select_own ON public.signals
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY signals_insert_own ON public.signals
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY signals_update_own ON public.signals
            FOR UPDATE USING (auth.uid() = user_id);
    """))

    # -- RLS: user_risk_settings (SELECT, INSERT, UPDATE) --
    op.execute(sa.text("ALTER TABLE public.user_risk_settings ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY user_risk_settings_select_own ON public.user_risk_settings
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY user_risk_settings_insert_own ON public.user_risk_settings
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY user_risk_settings_update_own ON public.user_risk_settings
            FOR UPDATE USING (auth.uid() = user_id);
    """))

    # -- RLS: risk_settings_changelog (SELECT, INSERT, UPDATE) --
    op.execute(sa.text("ALTER TABLE public.risk_settings_changelog ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY risk_settings_changelog_select_own ON public.risk_settings_changelog
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY risk_settings_changelog_insert_own ON public.risk_settings_changelog
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY risk_settings_changelog_update_own ON public.risk_settings_changelog
            FOR UPDATE USING (auth.uid() = user_id);
    """))

    # -- RLS: orders (SELECT, INSERT, UPDATE, DELETE) --
    op.execute(sa.text("ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY orders_select_own ON public.orders
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY orders_insert_own ON public.orders
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY orders_update_own ON public.orders
            FOR UPDATE USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY orders_delete_own ON public.orders
            FOR DELETE USING (auth.uid() = user_id);
    """))

    # -- RLS: positions (SELECT, INSERT, UPDATE) --
    op.execute(sa.text("ALTER TABLE public.positions ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY positions_select_own ON public.positions
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY positions_insert_own ON public.positions
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY positions_update_own ON public.positions
            FOR UPDATE USING (auth.uid() = user_id);
    """))

    # ================================================================
    # updated_at triggers (function already exists from migration 0005)
    # ================================================================
    for table in [
        "contract_specifications", "contract_calendar", "instrument_correlations",
        "webhook_urls", "signals", "user_risk_settings", "risk_check_audit",
        "risk_settings_changelog", "orders", "order_events", "positions",
    ]:
        op.execute(sa.text(f"""
            CREATE TRIGGER set_{table}_updated_at
                BEFORE UPDATE ON public.{table}
                FOR EACH ROW
                EXECUTE FUNCTION public.update_updated_at_column();
        """))


def downgrade() -> None:
    # Drop triggers
    for table in [
        "positions", "order_events", "orders", "risk_settings_changelog",
        "risk_check_audit", "user_risk_settings", "signals", "webhook_urls",
        "instrument_correlations", "contract_calendar", "contract_specifications",
    ]:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS set_{table}_updated_at ON public.{table};"))

    # Drop RLS policies: positions
    for policy in [
        "positions_update_own ON public.positions",
        "positions_insert_own ON public.positions",
        "positions_select_own ON public.positions",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.positions DISABLE ROW LEVEL SECURITY;"))

    # Drop RLS policies: orders
    for policy in [
        "orders_delete_own ON public.orders",
        "orders_update_own ON public.orders",
        "orders_insert_own ON public.orders",
        "orders_select_own ON public.orders",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.orders DISABLE ROW LEVEL SECURITY;"))

    # Drop RLS policies: risk_settings_changelog
    for policy in [
        "risk_settings_changelog_update_own ON public.risk_settings_changelog",
        "risk_settings_changelog_insert_own ON public.risk_settings_changelog",
        "risk_settings_changelog_select_own ON public.risk_settings_changelog",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.risk_settings_changelog DISABLE ROW LEVEL SECURITY;"))

    # Drop RLS policies: user_risk_settings
    for policy in [
        "user_risk_settings_update_own ON public.user_risk_settings",
        "user_risk_settings_insert_own ON public.user_risk_settings",
        "user_risk_settings_select_own ON public.user_risk_settings",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.user_risk_settings DISABLE ROW LEVEL SECURITY;"))

    # Drop RLS policies: signals
    for policy in [
        "signals_update_own ON public.signals",
        "signals_insert_own ON public.signals",
        "signals_select_own ON public.signals",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.signals DISABLE ROW LEVEL SECURITY;"))

    # Drop RLS policies: webhook_urls
    for policy in [
        "webhook_urls_delete_own ON public.webhook_urls",
        "webhook_urls_update_own ON public.webhook_urls",
        "webhook_urls_insert_own ON public.webhook_urls",
        "webhook_urls_select_own ON public.webhook_urls",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.webhook_urls DISABLE ROW LEVEL SECURITY;"))

    # Drop tables in reverse dependency order
    op.drop_table("positions")
    op.drop_table("order_events")
    op.drop_table("orders")
    op.drop_table("risk_settings_changelog")
    op.drop_table("risk_check_audit")
    op.drop_table("user_risk_settings")
    op.drop_table("signals")
    op.drop_table("webhook_urls")
    op.drop_table("instrument_correlations")
    op.drop_table("contract_calendar")
    op.drop_table("contract_specifications")
