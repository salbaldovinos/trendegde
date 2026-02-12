"""Integration tests for the trendline detection pipeline.

Tests the full flow: watchlist management, detection, config changes,
alert evaluation, dismissal, and state machine transitions.

Uses in-memory SQLite test data with mocked Celery tasks.
PostgreSQL-specific types (JSONB, UUID) are compiled to SQLite equivalents.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import String, event, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON, TypeDecorator

from app.db.base import Base
from app.db.models.alert import Alert
from app.db.models.candle import Candle
from app.db.models.instrument import Instrument
from app.db.models.pivot import Pivot
from app.db.models.trendline import Trendline
from app.db.models.trendline_event import TrendlineEvent
from app.db.models.user import User
from app.db.models.user_detection_config import UserDetectionConfig
from app.db.models.user_watchlist import UserWatchlist
from app.services.trendline_service import TrendlineService


# ---------------------------------------------------------------------------
# SQLite compatibility: compile PostgreSQL types to SQLite equivalents
# ---------------------------------------------------------------------------


def _patch_sqlite_type_compilers():
    """Register PostgreSQL type compilers on the SQLite dialect."""
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    if not hasattr(SQLiteTypeCompiler, "_patched_for_pg"):
        SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"  # type: ignore[attr-defined]
        SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "VARCHAR(36)"  # type: ignore[attr-defined]
        SQLiteTypeCompiler.visit_ARRAY = lambda self, type_, **kw: "TEXT"  # type: ignore[attr-defined]
        SQLiteTypeCompiler._patched_for_pg = True  # type: ignore[attr-defined]


def _create_tables_sqlite(conn):
    """Create tables with PostgreSQL server_defaults replaced for SQLite."""
    import re

    from sqlalchemy import MetaData, Table, Column, text as sa_text
    from sqlalchemy.schema import CreateTable

    for table in Base.metadata.sorted_tables:
        # Build raw DDL and fix PG-specific syntax
        create_stmt = CreateTable(table)
        raw_ddl = str(create_stmt.compile(dialect=conn.dialect))

        # Replace PostgreSQL-specific server defaults
        raw_ddl = re.sub(r"'[^']*'::jsonb", "'{}'", raw_ddl)
        raw_ddl = re.sub(r"gen_random_uuid\(\)", "(lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))", raw_ddl)
        raw_ddl = raw_ddl.replace("DEFAULT (now())", "DEFAULT (datetime('now'))")
        # Handle bare true/false defaults
        raw_ddl = re.sub(r"DEFAULT true\b", "DEFAULT 1", raw_ddl)
        raw_ddl = re.sub(r"DEFAULT false\b", "DEFAULT 0", raw_ddl)
        raw_ddl = re.sub(r"DEFAULT 'detected'", "DEFAULT 'detected'", raw_ddl)

        try:
            conn.execute(sa_text(raw_ddl))
        except Exception:
            # Table may already exist
            pass


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite DB with all tables, yield a session."""
    _patch_sqlite_type_compilers()

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Register PG-equivalent functions for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_functions(dbapi_conn, connection_record):
        dbapi_conn.create_function("now", 0, lambda: datetime.now(UTC).isoformat())
        dbapi_conn.create_function(
            "gen_random_uuid", 0,
            lambda: str(uuid.uuid4()),
        )

    # Patch onupdate to use Python callable instead of text("now()") for SQLite
    # This avoids MissingGreenlet errors with aiosqlite
    for table in Base.metadata.sorted_tables:
        for col in table.columns:
            if col.name == "updated_at" and col.onupdate is not None:
                col.onupdate = None  # Disable server-side onupdate for SQLite

    async with engine.begin() as conn:
        await conn.run_sync(_create_tables_sqlite)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    # Restore onupdate for other tests that might use PG
    from sqlalchemy import text as sa_text
    for table in Base.metadata.sorted_tables:
        for col in table.columns:
            if col.name == "updated_at" and col.onupdate is None:
                col.onupdate = sa_text("now()")

    await engine.dispose()


@pytest_asyncio.fixture
async def redis_mock():
    """Mock Redis client for TrendlineService."""
    mock = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    """Create base test data: user, instrument, candles."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="test@trendedge.io",
        display_name="Test Trader",
        subscription_tier="free",
    )
    db_session.add(user)

    instrument_id = uuid.uuid4()
    instrument = Instrument(
        id=instrument_id,
        symbol="CL",
        name="Crude Oil",
        exchange="NYMEX",
        asset_class="futures",
        tick_size=Decimal("0.01"),
        tick_value=Decimal("10.00"),
        contract_months="FGHJKMNQUVXZ",
        yahoo_symbol="CL=F",
    )
    db_session.add(instrument)

    # Create 60 daily candles with ATR
    now = datetime.now(UTC)
    candles = []
    for i in range(60):
        ts = now - timedelta(days=59 - i)
        candle = Candle(
            id=uuid.uuid4(),
            instrument_id=instrument_id,
            timestamp=ts,
            timeframe="1D",
            open=Decimal(str(70 + i * 0.1)),
            high=Decimal(str(72 + i * 0.1)),
            low=Decimal(str(68 + i * 0.1)),
            close=Decimal(str(71 + i * 0.1)),
            volume=10000 + i * 100,
            atr_14=Decimal("2.0000"),
        )
        candles.append(candle)
        db_session.add(candle)

    await db_session.commit()

    return {
        "user_id": user_id,
        "instrument_id": instrument_id,
        "candles": candles,
    }


def _create_trendline(
    user_id: uuid.UUID,
    instrument_id: uuid.UUID,
    pivot_1_id: uuid.UUID,
    pivot_2_id: uuid.UUID,
    *,
    status: str = "qualifying",
    grade: str = "A+",
    direction: str = "SUPPORT",
    composite_score: Decimal = Decimal("8.5000"),
    projected_price: Decimal | None = None,
    last_touch_at: datetime | None = None,
) -> Trendline:
    """Helper to create a Trendline ORM object."""
    return Trendline(
        id=uuid.uuid4(),
        user_id=user_id,
        instrument_id=instrument_id,
        direction=direction,
        status=status,
        grade=grade,
        anchor_pivot_1_id=pivot_1_id,
        anchor_pivot_2_id=pivot_2_id,
        slope_raw=Decimal("0.10000000"),
        slope_degrees=Decimal("5.71"),
        touch_count=4,
        touch_points=[],
        spacing_quality=Decimal("0.850"),
        composite_score=composite_score,
        duration_days=42,
        projected_price=projected_price or Decimal("75.0000"),
        safety_line_price=Decimal("68.0000"),
        last_touch_at=last_touch_at or datetime.now(UTC) - timedelta(days=7),
    )


async def _create_pivots(
    db_session: AsyncSession,
    instrument_id: uuid.UUID,
    candles: list[Candle],
    pivot_type: str = "LOW",
) -> tuple[uuid.UUID, uuid.UUID]:
    """Create two pivot records and return their IDs."""
    pivot_1 = Pivot(
        id=uuid.uuid4(),
        instrument_id=instrument_id,
        candle_id=candles[0].id,
        type=pivot_type,
        price=candles[0].low if pivot_type == "LOW" else candles[0].high,
        timestamp=candles[0].timestamp,
        n_bar_lookback=5,
    )
    pivot_2 = Pivot(
        id=uuid.uuid4(),
        instrument_id=instrument_id,
        candle_id=candles[20].id,
        type=pivot_type,
        price=candles[20].low if pivot_type == "LOW" else candles[20].high,
        timestamp=candles[20].timestamp,
        n_bar_lookback=5,
    )
    db_session.add(pivot_1)
    db_session.add(pivot_2)
    await db_session.flush()
    return pivot_1.id, pivot_2.id


# ===================================================================
# Test: Watchlist add triggers bootstrap + detection
# ===================================================================


class TestBootstrapAndDetect:
    @pytest.mark.asyncio
    async def test_bootstrap_and_detect(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Watchlist add dispatches bootstrap_instrument_task."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]

        svc = TrendlineService(db_session, redis_mock)

        with patch(
            "app.tasks.trendline_tasks.bootstrap_instrument_task"
        ) as mock_task:
            mock_task.delay = MagicMock()

            result = await svc.add_to_watchlist(user_id, instrument_id, "free")

            assert result["instrument_id"] == str(instrument_id)
            assert result["symbol"] == "CL"
            assert result["is_active"] is True
            mock_task.delay.assert_called_once_with(
                str(user_id), str(instrument_id)
            )

        # Verify watchlist entry was created
        stmt = select(UserWatchlist).where(
            UserWatchlist.user_id == user_id,
            UserWatchlist.instrument_id == instrument_id,
        )
        wl_result = await db_session.execute(stmt)
        entry = wl_result.scalar_one_or_none()
        assert entry is not None
        assert entry.is_active is True


# ===================================================================
# Test: Config update triggers recalculation
# ===================================================================


class TestConfigUpdateTriggersRecalc:
    @pytest.mark.asyncio
    async def test_config_update_triggers_recalc(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Changing detection config dispatches recalculate_all_trendlines."""
        user_id = seed_data["user_id"]

        svc = TrendlineService(db_session, redis_mock)

        with patch(
            "app.tasks.trendline_tasks.recalculate_all_trendlines"
        ) as mock_task:
            mock_task.delay = MagicMock()

            config = await svc.update_config(
                user_id, {"min_touch_count": 4, "max_slope_degrees": 40}
            )

            assert config["min_touch_count"] == 4
            assert config["max_slope_degrees"] == 40
            mock_task.delay.assert_called_once_with(str(user_id))

    @pytest.mark.asyncio
    async def test_reset_config_triggers_recalc(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Resetting config dispatches recalculate_all_trendlines."""
        user_id = seed_data["user_id"]

        svc = TrendlineService(db_session, redis_mock)

        # First create a config with non-default values
        with patch(
            "app.tasks.trendline_tasks.recalculate_all_trendlines"
        ) as mock_task:
            mock_task.delay = MagicMock()
            await svc.update_config(user_id, {"min_touch_count": 4})

        with patch(
            "app.tasks.trendline_tasks.recalculate_all_trendlines"
        ) as mock_task:
            mock_task.delay = MagicMock()

            config = await svc.reset_config(user_id)

            # Defaults are restored
            assert config["min_touch_count"] == 3
            mock_task.delay.assert_called_once_with(str(user_id))


# ===================================================================
# Test: Watchlist tier limits
# ===================================================================


class TestWatchlistTierLimits:
    @pytest.mark.asyncio
    async def test_free_tier_limit_3(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Free tier users cannot exceed 3 instruments on watchlist."""
        user_id = seed_data["user_id"]

        svc = TrendlineService(db_session, redis_mock)

        # Create 3 additional instruments and add them
        instrument_ids = []
        for i in range(3):
            inst = Instrument(
                id=uuid.uuid4(),
                symbol=f"T{i}",
                name=f"Test Instrument {i}",
                exchange="TEST",
                asset_class="futures",
                tick_size=Decimal("0.01"),
                tick_value=Decimal("10.00"),
                contract_months="FGHJKMNQUVXZ",
            )
            db_session.add(inst)
            instrument_ids.append(inst.id)
        await db_session.commit()

        with patch(
            "app.tasks.trendline_tasks.bootstrap_instrument_task"
        ) as mock_task:
            mock_task.delay = MagicMock()

            # Add 3 instruments (free limit)
            for inst_id in instrument_ids:
                await svc.add_to_watchlist(user_id, inst_id, "free")

            # 4th should fail
            extra_inst = Instrument(
                id=uuid.uuid4(),
                symbol="T4",
                name="Test Instrument 4",
                exchange="TEST",
                asset_class="futures",
                tick_size=Decimal("0.01"),
                tick_value=Decimal("10.00"),
                contract_months="FGHJKMNQUVXZ",
            )
            db_session.add(extra_inst)
            await db_session.commit()

            from app.core.exceptions import ForbiddenError

            with pytest.raises(ForbiddenError, match="Watchlist limit of 3"):
                await svc.add_to_watchlist(user_id, extra_inst.id, "free")

    @pytest.mark.asyncio
    async def test_trader_tier_limit_10(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Trader tier users cannot exceed 10 instruments on watchlist."""
        user_id = seed_data["user_id"]

        svc = TrendlineService(db_session, redis_mock)

        # Create 10 instruments
        instrument_ids = []
        for i in range(10):
            inst = Instrument(
                id=uuid.uuid4(),
                symbol=f"TR{i}",
                name=f"Trader Instrument {i}",
                exchange="TEST",
                asset_class="futures",
                tick_size=Decimal("0.01"),
                tick_value=Decimal("10.00"),
                contract_months="FGHJKMNQUVXZ",
            )
            db_session.add(inst)
            instrument_ids.append(inst.id)
        await db_session.commit()

        with patch(
            "app.tasks.trendline_tasks.bootstrap_instrument_task"
        ) as mock_task:
            mock_task.delay = MagicMock()

            for inst_id in instrument_ids:
                await svc.add_to_watchlist(user_id, inst_id, "trader")

            # 11th should fail
            extra_inst = Instrument(
                id=uuid.uuid4(),
                symbol="TR10",
                name="Trader Instrument 10",
                exchange="TEST",
                asset_class="futures",
                tick_size=Decimal("0.01"),
                tick_value=Decimal("10.00"),
                contract_months="FGHJKMNQUVXZ",
            )
            db_session.add(extra_inst)
            await db_session.commit()

            from app.core.exceptions import ForbiddenError

            with pytest.raises(ForbiddenError, match="Watchlist limit of 10"):
                await svc.add_to_watchlist(user_id, extra_inst.id, "trader")


# ===================================================================
# Test: Alert deduplication
# ===================================================================


class TestAlertDeduplication:
    @pytest.mark.asyncio
    async def test_alert_deduplication(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Same trendline break doesn't fire twice because trendline gets invalidated."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        # Create pivots for a RESISTANCE line using HIGH pivots.
        # Anchor pivot 1 at candle[0].high = 72.0, pivot 2 at candle[20].high = 74.0
        # slope_raw per candle = (74.0 - 72.0) / 20 = 0.1
        # At candle 59: line_price = 72.0 + 0.1 * 59 = 77.9
        # Latest candle close = ~76.9, which is below the line => no break for resistance
        #
        # To trigger a break, we need close ABOVE line for resistance.
        # Use a steep downward slope so the line is below current close.
        # Pivot at candles[0].high = 72.0 and candles[20].high = 74.0
        # We'll create pivots with custom low prices to make a support line that's
        # far above current close, triggering a break.
        #
        # Alternative approach: create a RESISTANCE line with slope that puts
        # line_price below close at candle[59].

        # Use HIGH pivots for resistance. Anchor at candle[40].high and candle[50].high
        # to make the slope go downward
        pivot_1 = Pivot(
            id=uuid.uuid4(),
            instrument_id=instrument_id,
            candle_id=candles[40].id,
            type="HIGH",
            price=Decimal("80.0000"),  # High price pivot
            timestamp=candles[40].timestamp,
            n_bar_lookback=5,
        )
        pivot_2 = Pivot(
            id=uuid.uuid4(),
            instrument_id=instrument_id,
            candle_id=candles[50].id,
            type="HIGH",
            price=Decimal("75.0000"),  # Declining price
            timestamp=candles[50].timestamp,
            n_bar_lookback=5,
        )
        db_session.add(pivot_1)
        db_session.add(pivot_2)
        await db_session.flush()

        # slope_raw = (75 - 80) / (50 - 40) = -0.5 per candle
        # At candle 59: line_price = 80.0 + (-0.5) * (59 - 40) = 80.0 - 9.5 = 70.5
        # Latest candle close = ~76.9 which is ABOVE the resistance line => BREAK
        trendline = Trendline(
            id=uuid.uuid4(),
            user_id=user_id,
            instrument_id=instrument_id,
            direction="RESISTANCE",
            status="qualifying",
            grade="A+",
            anchor_pivot_1_id=pivot_1.id,
            anchor_pivot_2_id=pivot_2.id,
            slope_raw=Decimal("-0.50000000"),
            slope_degrees=Decimal("26.57"),
            touch_count=3,
            touch_points=[],
            spacing_quality=Decimal("0.850"),
            composite_score=Decimal("8.5000"),
            duration_days=42,
            projected_price=Decimal("70.5000"),
            safety_line_price=Decimal("68.0000"),
            last_touch_at=datetime.now(UTC) - timedelta(days=7),
        )
        db_session.add(trendline)
        await db_session.commit()

        svc = TrendlineService(db_session, redis_mock)

        # First evaluation: should create a break alert and invalidate the trendline
        latest_candle = candles[-1]
        alerts_1 = await svc.evaluate_alerts(
            user_id, instrument_id, latest_candle.id
        )

        # The close is above the resistance line => break
        break_alerts = [a for a in alerts_1 if a["alert_type"] == "break"]
        assert len(break_alerts) == 1

        # Verify trendline is now invalidated
        await db_session.refresh(trendline)
        assert trendline.status == "invalidated"

        # Second evaluation with same candle: no alerts because trendline is invalidated
        alerts_2 = await svc.evaluate_alerts(
            user_id, instrument_id, latest_candle.id
        )
        assert len(alerts_2) == 0


# ===================================================================
# Test: Dismiss trendline
# ===================================================================


class TestDismissTrendline:
    @pytest.mark.asyncio
    async def test_dismiss_qualifying_trendline(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Qualifying trendline can be dismissed to invalidated."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        pivot_1_id, pivot_2_id = await _create_pivots(
            db_session, instrument_id, candles
        )

        trendline = _create_trendline(
            user_id, instrument_id, pivot_1_id, pivot_2_id, status="qualifying"
        )
        db_session.add(trendline)
        await db_session.commit()

        svc = TrendlineService(db_session, redis_mock)
        result = await svc.dismiss_trendline(
            user_id, trendline.id, reason="Not relevant"
        )

        assert result["status"] == "invalidated"
        assert result["invalidation_reason"] == "Not relevant"

        # Verify event was logged
        events_stmt = select(TrendlineEvent).where(
            TrendlineEvent.trendline_id == trendline.id
        )
        events_result = await db_session.execute(events_stmt)
        events = events_result.scalars().all()
        assert len(events) == 1
        assert events[0].event_type == "state_change"

    @pytest.mark.asyncio
    async def test_dismiss_active_trendline(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Active trendline can be dismissed to invalidated."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        pivot_1_id, pivot_2_id = await _create_pivots(
            db_session, instrument_id, candles
        )

        trendline = _create_trendline(
            user_id, instrument_id, pivot_1_id, pivot_2_id, status="active"
        )
        db_session.add(trendline)
        await db_session.commit()

        svc = TrendlineService(db_session, redis_mock)
        result = await svc.dismiss_trendline(user_id, trendline.id)

        assert result["status"] == "invalidated"

    @pytest.mark.asyncio
    async def test_dismiss_invalidated_fails(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Cannot dismiss an already invalidated trendline."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        pivot_1_id, pivot_2_id = await _create_pivots(
            db_session, instrument_id, candles
        )

        trendline = _create_trendline(
            user_id, instrument_id, pivot_1_id, pivot_2_id, status="active"
        )
        trendline.status = "invalidated"
        trendline.invalidation_reason = "Previously dismissed"
        db_session.add(trendline)
        await db_session.commit()

        svc = TrendlineService(db_session, redis_mock)

        from app.core.exceptions import ConflictError

        with pytest.raises(ConflictError):
            await svc.dismiss_trendline(user_id, trendline.id)


# ===================================================================
# Test: Full lifecycle state machine traversal
# ===================================================================


class TestTrendlineLifecycle:
    @pytest.mark.asyncio
    async def test_trendline_lifecycle(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Full state machine: qualifying -> active -> qualifying -> expired.

        Note: promote_or_demote calculates distance from anchor pivot projection,
        not from trendline.projected_price field. So we test promotion with
        a near-price line and demotion by changing the anchor pivot's price
        to make the projected line far from current close.
        """
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        # Step 1: Create a trendline close to current price for PROMOTION
        # anchor at candle[0], candle close = ~71.0
        # Latest candle close = ~76.9, ATR = 2.0
        # We need line_price at candle[59] within 3*ATR (6.0) of 76.9 => [70.9, 82.9]
        # pivot_price = 76.9, slope = 0.0 (horizontal) => line_price = 76.9 at all candles
        pivot_close = Pivot(
            id=uuid.uuid4(),
            instrument_id=instrument_id,
            candle_id=candles[0].id,
            type="LOW",
            price=candles[-1].close,  # ~76.9
            timestamp=candles[0].timestamp,
            n_bar_lookback=5,
        )
        pivot_close_2 = Pivot(
            id=uuid.uuid4(),
            instrument_id=instrument_id,
            candle_id=candles[20].id,
            type="LOW",
            price=candles[-1].close,  # Same price = horizontal
            timestamp=candles[20].timestamp,
            n_bar_lookback=5,
        )
        db_session.add(pivot_close)
        db_session.add(pivot_close_2)
        await db_session.flush()

        trendline = Trendline(
            id=uuid.uuid4(),
            user_id=user_id,
            instrument_id=instrument_id,
            direction="SUPPORT",
            status="qualifying",
            grade="A+",
            anchor_pivot_1_id=pivot_close.id,
            anchor_pivot_2_id=pivot_close_2.id,
            slope_raw=Decimal("0.00000000"),
            slope_degrees=Decimal("0.00"),
            touch_count=4,
            touch_points=[],
            spacing_quality=Decimal("0.850"),
            composite_score=Decimal("8.5000"),
            duration_days=42,
            projected_price=candles[-1].close,
            safety_line_price=Decimal("68.0000"),
            last_touch_at=datetime.now(UTC) - timedelta(days=7),
        )
        db_session.add(trendline)
        await db_session.commit()
        tl_id = trendline.id

        svc = TrendlineService(db_session, redis_mock)

        # Step 1: Promote qualifying -> active (A+ within 3*ATR)
        result = await svc.promote_or_demote_trendlines(user_id, instrument_id)
        assert result["promoted"] >= 1

        await db_session.refresh(trendline)
        assert trendline.status == "active"

        # Step 2: Demote active -> qualifying
        # Change the anchor pivot price so line projects far from current close
        # Set pivot price to 50.0 => line at 50.0, close at ~76.9, distance = 26.9
        # 3*ATR = 6.0, so 26.9 > 6.0 => demotion triggered
        pivot_close.price = Decimal("50.0000")
        await db_session.commit()

        result = await svc.promote_or_demote_trendlines(user_id, instrument_id)
        assert result["demoted"] >= 1

        await db_session.refresh(trendline)
        assert trendline.status == "qualifying"

        # Step 3: Expire (set last_touch_at to 7 months ago)
        trendline.last_touch_at = datetime.now(UTC) - timedelta(days=210)
        await db_session.commit()

        expired = await svc.expire_stale_trendlines()
        assert expired >= 1

        await db_session.refresh(trendline)
        assert trendline.status == "expired"

        # Verify all state transitions are logged
        events_stmt = (
            select(TrendlineEvent)
            .where(TrendlineEvent.trendline_id == tl_id)
            .order_by(TrendlineEvent.created_at.asc())
        )
        events_result = await db_session.execute(events_stmt)
        events = events_result.scalars().all()
        assert len(events) == 3  # promote, demote, expire

    @pytest.mark.asyncio
    async def test_promote_requires_a_plus_grade(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Only A+ grade trendlines are promoted, not A or B."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        pivot_1_id, pivot_2_id = await _create_pivots(
            db_session, instrument_id, candles
        )

        # A-grade trendline close to price
        trendline = _create_trendline(
            user_id,
            instrument_id,
            pivot_1_id,
            pivot_2_id,
            status="qualifying",
            grade="A",
            projected_price=candles[-1].close,
        )
        db_session.add(trendline)
        await db_session.commit()

        svc = TrendlineService(db_session, redis_mock)
        result = await svc.promote_or_demote_trendlines(user_id, instrument_id)

        assert result["promoted"] == 0

        await db_session.refresh(trendline)
        assert trendline.status == "qualifying"

    @pytest.mark.asyncio
    async def test_proximity_score_decay(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Trendlines far from current price get decayed composite scores."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        pivot_1_id, pivot_2_id = await _create_pivots(
            db_session, instrument_id, candles
        )

        # Close trendline (within 5*ATR)
        close_tl = _create_trendline(
            user_id,
            instrument_id,
            pivot_1_id,
            pivot_2_id,
            status="qualifying",
            composite_score=Decimal("10.0000"),
            projected_price=candles[-1].close,  # Right at current price
        )

        # Far trendline (beyond 5*ATR, ATR=2.0 so threshold=10)
        far_tl = _create_trendline(
            user_id,
            instrument_id,
            pivot_1_id,
            pivot_2_id,
            status="qualifying",
            composite_score=Decimal("10.0000"),
            projected_price=candles[-1].close + Decimal("20.0000"),
        )

        db_session.add(close_tl)
        db_session.add(far_tl)
        await db_session.commit()

        svc = TrendlineService(db_session, redis_mock)
        result = await svc.get_active_trendlines(user_id, instrument_id)

        all_tls = result["support"] + result["resistance"]
        close_entry = next(d for d in all_tls if d["id"] == str(close_tl.id))
        far_entry = next(d for d in all_tls if d["id"] == str(far_tl.id))

        # Close trendline should keep its score (within 5*ATR)
        assert close_entry["composite_score"] == pytest.approx(10.0, rel=0.01)

        # Far trendline: distance=20, 5*ATR=10, decay = 10/20 = 0.5, score = 10*0.5 = 5.0
        assert far_entry["composite_score"] < 10.0
        assert far_entry["composite_score"] == pytest.approx(5.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_dismiss_not_found(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Dismissing a non-existent trendline raises NotFoundError."""
        user_id = seed_data["user_id"]

        svc = TrendlineService(db_session, redis_mock)

        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await svc.dismiss_trendline(user_id, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_expire_does_not_affect_invalidated(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Already invalidated trendlines should not be expired."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]
        candles = seed_data["candles"]

        pivot_1_id, pivot_2_id = await _create_pivots(
            db_session, instrument_id, candles
        )

        trendline = _create_trendline(
            user_id,
            instrument_id,
            pivot_1_id,
            pivot_2_id,
            status="active",
            last_touch_at=datetime.now(UTC) - timedelta(days=210),
        )
        trendline.status = "invalidated"
        trendline.invalidation_reason = "Previously dismissed"
        db_session.add(trendline)
        await db_session.commit()

        svc = TrendlineService(db_session, redis_mock)
        expired = await svc.expire_stale_trendlines()

        assert expired == 0

        await db_session.refresh(trendline)
        assert trendline.status == "invalidated"

    @pytest.mark.asyncio
    async def test_watchlist_remove_soft_delete(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Removing from watchlist soft-deletes (is_active=false)."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]

        svc = TrendlineService(db_session, redis_mock)

        with patch(
            "app.tasks.trendline_tasks.bootstrap_instrument_task"
        ) as mock_task:
            mock_task.delay = MagicMock()
            await svc.add_to_watchlist(user_id, instrument_id, "free")

        result = await svc.remove_from_watchlist(user_id, instrument_id)
        assert result["is_active"] is False

        # Verify soft delete
        stmt = select(UserWatchlist).where(
            UserWatchlist.user_id == user_id,
            UserWatchlist.instrument_id == instrument_id,
        )
        wl_result = await db_session.execute(stmt)
        entry = wl_result.scalar_one_or_none()
        assert entry is not None
        assert entry.is_active is False

    @pytest.mark.asyncio
    async def test_watchlist_reactivation(
        self, db_session: AsyncSession, redis_mock, seed_data
    ):
        """Re-adding a soft-deleted watchlist entry reactivates it."""
        user_id = seed_data["user_id"]
        instrument_id = seed_data["instrument_id"]

        svc = TrendlineService(db_session, redis_mock)

        with patch(
            "app.tasks.trendline_tasks.bootstrap_instrument_task"
        ) as mock_task:
            mock_task.delay = MagicMock()

            await svc.add_to_watchlist(user_id, instrument_id, "free")
            await svc.remove_from_watchlist(user_id, instrument_id)

            # Re-add
            result = await svc.add_to_watchlist(user_id, instrument_id, "free")
            assert result["is_active"] is True
