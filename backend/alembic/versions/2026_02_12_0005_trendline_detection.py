"""Trendline detection engine tables: instruments, candles, pivots, trendlines,
trendline_events, alerts, user_detection_config, user_watchlist.

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- instruments table (shared reference, no RLS) --
    op.create_table(
        "instruments",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("exchange", sa.String(20), nullable=False),
        sa.Column("asset_class", sa.String(20), nullable=False, server_default=sa.text("'futures'")),
        sa.Column("tick_size", sa.Numeric(10, 4), nullable=False),
        sa.Column("tick_value", sa.Numeric(10, 4), nullable=False),
        sa.Column("contract_months", sa.String(24), nullable=False),
        sa.Column("current_contract", sa.String(20), nullable=True),
        sa.Column("roll_date", sa.Date(), nullable=True),
        sa.Column("yahoo_symbol", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_instruments"),
    )
    op.create_index("uq_instruments_symbol", "instruments", ["symbol"], unique=True)

    # -- candles table (shared data, no RLS) --
    op.create_table(
        "candles",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("instrument_id", UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timeframe", sa.String(5), nullable=False),
        sa.Column("open", sa.Numeric(12, 4), nullable=False),
        sa.Column("high", sa.Numeric(12, 4), nullable=False),
        sa.Column("low", sa.Numeric(12, 4), nullable=False),
        sa.Column("close", sa.Numeric(12, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("source", sa.String(20), nullable=False, server_default=sa.text("'yfinance'")),
        sa.Column("atr_14", sa.Numeric(12, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_candles"),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"],
            name="fk_candles_instrument_id_instruments", ondelete="CASCADE",
        ),
        sa.CheckConstraint("high >= low", name="valid_high_low"),
        sa.CheckConstraint("volume >= 0", name="valid_volume"),
    )
    op.create_index(
        "uq_candles_instrument_ts_tf", "candles",
        ["instrument_id", "timestamp", "timeframe"], unique=True,
    )
    op.create_index("ix_candles_instrument_id", "candles", ["instrument_id"])
    op.create_index("ix_candles_timestamp", "candles", ["timestamp"])

    # -- pivots table (shared data, no RLS) --
    op.create_table(
        "pivots",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("instrument_id", UUID(as_uuid=True), nullable=False),
        sa.Column("candle_id", UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(4), nullable=False),
        sa.Column("price", sa.Numeric(12, 4), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("n_bar_lookback", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_pivots"),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"],
            name="fk_pivots_instrument_id_instruments", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["candle_id"], ["candles.id"],
            name="fk_pivots_candle_id_candles", ondelete="CASCADE",
        ),
        sa.CheckConstraint("type IN ('HIGH', 'LOW')", name="valid_pivot_type"),
        sa.CheckConstraint("n_bar_lookback BETWEEN 2 AND 10", name="valid_n_bar"),
    )
    op.create_index("ix_pivots_instrument_id", "pivots", ["instrument_id"])
    op.create_index("ix_pivots_candle_id", "pivots", ["candle_id"])
    op.create_index("ix_pivots_type", "pivots", ["type"])

    # -- trendlines table (user-owned, RLS) --
    op.create_table(
        "trendlines",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("instrument_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'detected'")),
        sa.Column("grade", sa.String(2), nullable=True),
        sa.Column("anchor_pivot_1_id", UUID(as_uuid=True), nullable=False),
        sa.Column("anchor_pivot_2_id", UUID(as_uuid=True), nullable=False),
        sa.Column("slope_raw", sa.Numeric(16, 8), nullable=False),
        sa.Column("slope_degrees", sa.Numeric(6, 2), nullable=False),
        sa.Column("touch_count", sa.SmallInteger(), nullable=False, server_default=sa.text("2")),
        sa.Column("touch_points", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("spacing_quality", sa.Numeric(4, 3), nullable=True),
        sa.Column("composite_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("projected_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("safety_line_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.Column("last_touch_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_trendlines"),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"],
            name="fk_trendlines_instrument_id_instruments", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_trendlines_user_id_users", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["anchor_pivot_1_id"], ["pivots.id"],
            name="fk_trendlines_anchor_pivot_1_id_pivots", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["anchor_pivot_2_id"], ["pivots.id"],
            name="fk_trendlines_anchor_pivot_2_id_pivots", ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "direction IN ('SUPPORT', 'RESISTANCE')", name="valid_direction",
        ),
        sa.CheckConstraint(
            "status IN ('detected', 'qualifying', 'active', 'traded', 'invalidated', 'expired')",
            name="valid_trendline_status",
        ),
        sa.CheckConstraint("grade IS NULL OR grade IN ('A+', 'A', 'B')", name="valid_grade"),
    )
    op.create_index("ix_trendlines_user_id", "trendlines", ["user_id"])
    op.create_index("ix_trendlines_instrument_id", "trendlines", ["instrument_id"])
    op.create_index("ix_trendlines_status", "trendlines", ["status"])
    op.create_index(
        "ix_trendlines_user_instrument_status", "trendlines",
        ["user_id", "instrument_id", "status"],
    )

    # -- trendline_events table (no RLS) --
    op.create_table(
        "trendline_events",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("trendline_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("old_value", JSONB(), nullable=True),
        sa.Column("new_value", JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("trigger_candle_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_trendline_events"),
        sa.ForeignKeyConstraint(
            ["trendline_id"], ["trendlines.id"],
            name="fk_trendline_events_trendline_id_trendlines", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trigger_candle_id"], ["candles.id"],
            name="fk_trendline_events_trigger_candle_id_candles", ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "event_type IN ('state_change', 'touch_added', 'grade_change', 'score_update')",
            name="valid_event_type",
        ),
    )
    op.create_index("ix_trendline_events_trendline_id", "trendline_events", ["trendline_id"])
    op.create_index("ix_trendline_events_created_at", "trendline_events", ["created_at"])

    # -- alerts table (user-owned, RLS) --
    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("trendline_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=True),
        sa.Column("trigger_candle_id", UUID(as_uuid=True), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("channels_sent", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_alerts"),
        sa.ForeignKeyConstraint(
            ["trendline_id"], ["trendlines.id"],
            name="fk_alerts_trendline_id_trendlines", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_alerts_user_id_users", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trigger_candle_id"], ["candles.id"],
            name="fk_alerts_trigger_candle_id_candles", ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "alert_type IN ('break', 'touch', 'new_a_plus', 'invalidated')",
            name="valid_alert_type",
        ),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])
    op.create_index("ix_alerts_trendline_id", "alerts", ["trendline_id"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    # Unique constraint for break/invalidation dedup (only one per trendline)
    op.create_index(
        "uq_alerts_trendline_break", "alerts",
        ["trendline_id", "alert_type"],
        unique=True,
        postgresql_where=sa.text("alert_type IN ('break', 'invalidated', 'new_a_plus')"),
    )
    # Unique constraint for touch dedup (one per trendline per candle)
    op.create_index(
        "uq_alerts_trendline_touch_candle", "alerts",
        ["trendline_id", "alert_type", "trigger_candle_id"],
        unique=True,
        postgresql_where=sa.text("alert_type = 'touch'"),
    )

    # -- user_detection_config table (user-owned, RLS) --
    op.create_table(
        "user_detection_config",
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("min_touch_count", sa.SmallInteger(), nullable=False, server_default=sa.text("3")),
        sa.Column("min_candle_spacing", sa.SmallInteger(), nullable=False, server_default=sa.text("6")),
        sa.Column("max_slope_degrees", sa.SmallInteger(), nullable=False, server_default=sa.text("45")),
        sa.Column("min_duration_days", sa.SmallInteger(), nullable=False, server_default=sa.text("21")),
        sa.Column("touch_tolerance_atr", sa.Numeric(3, 1), nullable=False, server_default=sa.text("0.5")),
        sa.Column("pivot_n_bar_lookback", sa.SmallInteger(), nullable=False, server_default=sa.text("5")),
        sa.Column("max_lines_per_instrument", sa.SmallInteger(), nullable=False, server_default=sa.text("5")),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.Column("quiet_hours_timezone", sa.String(50), nullable=True),
        sa.Column("preset_name", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_user_detection_config"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_user_detection_config_user_id_users", ondelete="CASCADE",
        ),
        sa.CheckConstraint("min_touch_count BETWEEN 2 AND 5", name="valid_min_touch_count"),
        sa.CheckConstraint("min_candle_spacing BETWEEN 3 AND 20", name="valid_min_candle_spacing"),
        sa.CheckConstraint("max_slope_degrees BETWEEN 15 AND 75", name="valid_max_slope_degrees"),
        sa.CheckConstraint("min_duration_days BETWEEN 7 AND 180", name="valid_min_duration_days"),
        sa.CheckConstraint("touch_tolerance_atr BETWEEN 0.2 AND 1.5", name="valid_touch_tolerance"),
        sa.CheckConstraint("pivot_n_bar_lookback BETWEEN 2 AND 10", name="valid_pivot_lookback"),
        sa.CheckConstraint("max_lines_per_instrument BETWEEN 1 AND 10", name="valid_max_lines"),
    )

    # -- user_watchlist table (user-owned, RLS) --
    op.create_table(
        "user_watchlist",
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "instrument_id", name="pk_user_watchlist"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_user_watchlist_user_id_users", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"],
            name="fk_user_watchlist_instrument_id_instruments", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_user_watchlist_user_id", "user_watchlist", ["user_id"])

    # -- Row-Level Security: trendlines --
    op.execute(sa.text("ALTER TABLE public.trendlines ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY trendlines_select_own ON public.trendlines
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY trendlines_insert_own ON public.trendlines
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY trendlines_update_own ON public.trendlines
            FOR UPDATE USING (auth.uid() = user_id);
    """))

    # -- Row-Level Security: alerts --
    op.execute(sa.text("ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY alerts_select_own ON public.alerts
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY alerts_insert_own ON public.alerts
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY alerts_update_own ON public.alerts
            FOR UPDATE USING (auth.uid() = user_id);
    """))

    # -- Row-Level Security: user_detection_config --
    op.execute(sa.text("ALTER TABLE public.user_detection_config ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY user_detection_config_select_own ON public.user_detection_config
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY user_detection_config_insert_own ON public.user_detection_config
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY user_detection_config_update_own ON public.user_detection_config
            FOR UPDATE USING (auth.uid() = user_id);
    """))

    # -- Row-Level Security: user_watchlist --
    op.execute(sa.text("ALTER TABLE public.user_watchlist ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY user_watchlist_select_own ON public.user_watchlist
            FOR SELECT USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY user_watchlist_insert_own ON public.user_watchlist
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY user_watchlist_update_own ON public.user_watchlist
            FOR UPDATE USING (auth.uid() = user_id);
    """))
    op.execute(sa.text("""
        CREATE POLICY user_watchlist_delete_own ON public.user_watchlist
            FOR DELETE USING (auth.uid() = user_id);
    """))

    # -- Seed Phase 1 instruments --
    op.execute(sa.text("""
        INSERT INTO instruments (symbol, name, exchange, tick_size, tick_value, contract_months, yahoo_symbol)
        VALUES
            ('CL', 'Crude Oil', 'NYMEX', 0.01, 10.00, 'FGHJKMNQUVXZ', 'CL=F'),
            ('GC', 'Gold', 'COMEX', 0.10, 10.00, 'GJMQVZ', 'GC=F'),
            ('PL', 'Platinum', 'NYMEX', 0.10, 5.00, 'FJNV', 'PL=F'),
            ('YM', 'E-mini Dow', 'CBOT', 1.00, 5.00, 'HMUZ', 'YM=F'),
            ('MES', 'Micro E-mini S&P 500', 'CME', 0.25, 1.25, 'HMUZ', 'ES=F'),
            ('MNQ', 'Micro E-mini Nasdaq 100', 'CME', 0.25, 0.50, 'HMUZ', 'NQ=F')
        ON CONFLICT DO NOTHING;
    """))

    # -- updated_at trigger function (shared) --
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION public.update_updated_at_column()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$;
    """))

    # Apply updated_at triggers to all new tables
    for table in [
        "instruments", "candles", "pivots", "trendlines",
        "trendline_events", "alerts", "user_detection_config", "user_watchlist",
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
        "user_watchlist", "user_detection_config", "alerts", "trendline_events",
        "trendlines", "pivots", "candles", "instruments",
    ]:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS set_{table}_updated_at ON public.{table};"))

    op.execute(sa.text("DROP FUNCTION IF EXISTS public.update_updated_at_column();"))

    # Drop RLS policies
    for policy in [
        "user_watchlist_delete_own ON public.user_watchlist",
        "user_watchlist_update_own ON public.user_watchlist",
        "user_watchlist_insert_own ON public.user_watchlist",
        "user_watchlist_select_own ON public.user_watchlist",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.user_watchlist DISABLE ROW LEVEL SECURITY;"))

    for policy in [
        "user_detection_config_update_own ON public.user_detection_config",
        "user_detection_config_insert_own ON public.user_detection_config",
        "user_detection_config_select_own ON public.user_detection_config",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.user_detection_config DISABLE ROW LEVEL SECURITY;"))

    for policy in [
        "alerts_update_own ON public.alerts",
        "alerts_insert_own ON public.alerts",
        "alerts_select_own ON public.alerts",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.alerts DISABLE ROW LEVEL SECURITY;"))

    for policy in [
        "trendlines_update_own ON public.trendlines",
        "trendlines_insert_own ON public.trendlines",
        "trendlines_select_own ON public.trendlines",
    ]:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy};"))
    op.execute(sa.text("ALTER TABLE public.trendlines DISABLE ROW LEVEL SECURITY;"))

    # Drop tables in reverse dependency order
    op.drop_table("user_watchlist")
    op.drop_table("user_detection_config")
    op.drop_table("alerts")
    op.drop_table("trendline_events")
    op.drop_table("trendlines")
    op.drop_table("pivots")
    op.drop_table("candles")
    op.drop_table("instruments")
