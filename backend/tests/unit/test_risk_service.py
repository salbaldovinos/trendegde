"""Unit tests for the risk service (8 risk checks, circuit breaker, quantity calculation)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.db.models.contract_specification import ContractSpecification
from app.db.models.instrument_correlation import InstrumentCorrelation
from app.db.models.position import Position
from app.db.models.signal import Signal
from app.services.risk_service import RiskService


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

_USER_ID = uuid.uuid4()


def make_signal(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "user_id": _USER_ID,
        "source": "MANUAL",
        "status": "ENRICHED",
        "instrument_symbol": "MNQ",
        "direction": "LONG",
        "entry_type": "MARKET",
        "entry_price": Decimal("18500.00"),
        "stop_loss_price": Decimal("18480.00"),
        "take_profit_price": Decimal("18540.00"),
        "quantity": 1,
        "enrichment_data": {"risk_per_contract": 40.0, "risk_reward_ratio": 2.0},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    signal = MagicMock(spec=Signal)
    for k, v in defaults.items():
        setattr(signal, k, v)
    return signal


def make_contract_spec(**overrides):
    defaults = {
        "symbol": "MNQ",
        "tick_size": Decimal("0.25"),
        "tick_value": Decimal("0.50"),
        "point_value": Decimal("2.00"),
        "is_micro": True,
        "full_size_symbol": "NQ",
    }
    defaults.update(overrides)
    spec = MagicMock(spec=ContractSpecification)
    for k, v in defaults.items():
        setattr(spec, k, v)
    return spec


def default_settings(**overrides):
    settings = {
        "max_position_size_micro": 2,
        "max_position_size_full": 1,
        "daily_loss_limit": 500.0,
        "max_concurrent_positions": 3,
        "min_risk_reward": 2.0,
        "correlation_limit": 0.70,
        "max_single_trade_risk": 200.0,
        "trading_hours_mode": "RTH",
        "staleness_minutes": 5,
        "paper_slippage_ticks": 1,
        "circuit_breaker_threshold": 3,
        "is_paper_mode": True,
    }
    settings.update(overrides)
    return settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest_asyncio.fixture
async def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.hincrby = AsyncMock(return_value=1)
    redis.hset = AsyncMock()
    return redis


@pytest_asyncio.fixture
async def svc(mock_db, mock_redis):
    return RiskService(mock_db, mock_redis)


# ═══════════════════════════════════════════════════════════════════
# Max Position Size Tests
# ═══════════════════════════════════════════════════════════════════


class TestMaxPositionSize:
    """Test max position size per instrument."""

    @pytest.mark.asyncio
    async def test_pass_under_limit(self, svc, mock_db):
        """Pass when current + new is under limit."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0  # No current positions
        mock_db.execute.return_value = mock_result

        signal = make_signal(quantity=1)
        spec = make_contract_spec(is_micro=True)
        settings = default_settings(max_position_size_micro=2)

        result = await svc.check_max_position_size(signal, settings, spec)
        assert result["result"] == "PASS"
        assert result["actual_value"] == 1

    @pytest.mark.asyncio
    async def test_fail_over_limit(self, svc, mock_db):
        """Fail when current + new exceeds limit."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2  # Already at limit
        mock_db.execute.return_value = mock_result

        signal = make_signal(quantity=1)
        spec = make_contract_spec(is_micro=True)
        settings = default_settings(max_position_size_micro=2)

        result = await svc.check_max_position_size(signal, settings, spec)
        assert result["result"] == "FAIL"
        assert result["actual_value"] == 3


# ═══════════════════════════════════════════════════════════════════
# Daily Loss Limit Tests
# ═══════════════════════════════════════════════════════════════════


class TestDailyLossLimit:
    """Test daily loss limit check."""

    @pytest.mark.asyncio
    async def test_pass_under_limit(self, svc, mock_db):
        """Pass when total exposure is under daily limit."""
        # realized losses = 0, unrealized = 0, worst case = 40
        mock_result1 = MagicMock()
        mock_result1.scalar.return_value = Decimal("0")
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = Decimal("0")
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        signal = make_signal(enrichment_data={"risk_per_contract": 40.0})
        spec = make_contract_spec()
        settings = default_settings(daily_loss_limit=500.0)

        result = await svc.check_daily_loss_limit(signal, settings, spec)
        assert result["result"] == "PASS"

    @pytest.mark.asyncio
    async def test_fail_over_limit(self, svc, mock_db):
        """Fail when total exposure exceeds daily limit."""
        # realized losses = -400, unrealized = -80, worst case = 40
        mock_result1 = MagicMock()
        mock_result1.scalar.return_value = Decimal("-400")
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = Decimal("-80")
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        signal = make_signal(enrichment_data={"risk_per_contract": 40.0})
        spec = make_contract_spec()
        settings = default_settings(daily_loss_limit=500.0)

        result = await svc.check_daily_loss_limit(signal, settings, spec)
        assert result["result"] == "FAIL"
        # 400 + 80 + 40 = 520 > 500
        assert result["actual_value"] == 520.0


# ═══════════════════════════════════════════════════════════════════
# Max Concurrent Positions Tests
# ═══════════════════════════════════════════════════════════════════


class TestMaxConcurrentPositions:
    """Test max concurrent positions check."""

    @pytest.mark.asyncio
    async def test_pass_under_limit(self, svc, mock_db):
        """Pass when count is under max."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute.return_value = mock_result

        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(max_concurrent_positions=3)

        result = await svc.check_max_concurrent_positions(signal, settings, spec)
        assert result["result"] == "PASS"

    @pytest.mark.asyncio
    async def test_fail_at_limit(self, svc, mock_db):
        """Fail when already at max concurrent limit."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_db.execute.return_value = mock_result

        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(max_concurrent_positions=3)

        result = await svc.check_max_concurrent_positions(signal, settings, spec)
        assert result["result"] == "FAIL"


# ═══════════════════════════════════════════════════════════════════
# Min Risk/Reward Tests
# ═══════════════════════════════════════════════════════════════════


class TestMinRiskReward:
    """Test minimum risk/reward ratio check."""

    @pytest.mark.asyncio
    async def test_pass_good_rr(self, svc, mock_db):
        """Pass with R:R at or above threshold."""
        signal = make_signal(enrichment_data={"risk_reward_ratio": 2.5})
        spec = make_contract_spec()
        settings = default_settings(min_risk_reward=2.0)

        result = await svc.check_min_risk_reward(signal, settings, spec)
        assert result["result"] == "PASS"

    @pytest.mark.asyncio
    async def test_fail_bad_rr(self, svc, mock_db):
        """Fail with R:R below threshold."""
        signal = make_signal(enrichment_data={"risk_reward_ratio": 1.5})
        spec = make_contract_spec()
        settings = default_settings(min_risk_reward=2.0)

        result = await svc.check_min_risk_reward(signal, settings, spec)
        assert result["result"] == "FAIL"
        assert result["actual_value"] == 1.5

    @pytest.mark.asyncio
    async def test_warn_no_rr(self, svc, mock_db):
        """Warn when no R:R ratio available."""
        signal = make_signal(enrichment_data={})
        spec = make_contract_spec()
        settings = default_settings(min_risk_reward=2.0)

        result = await svc.check_min_risk_reward(signal, settings, spec)
        assert result["result"] == "WARN"

    @pytest.mark.asyncio
    async def test_skip_disabled(self, svc, mock_db):
        """Skip when min_risk_reward is 0 (disabled)."""
        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(min_risk_reward=0)

        result = await svc.check_min_risk_reward(signal, settings, spec)
        assert result["result"] == "SKIP"


# ═══════════════════════════════════════════════════════════════════
# Correlation Tests
# ═══════════════════════════════════════════════════════════════════


class TestCorrelation:
    """Test instrument correlation check."""

    @pytest.mark.asyncio
    async def test_pass_no_correlation(self, svc, mock_db):
        """Pass when no open positions exist."""
        # First call: _normalize_symbol for signal
        spec_result = MagicMock()
        spec_result.scalar_one_or_none.return_value = make_contract_spec(full_size_symbol="NQ")

        # Second call: get open position symbols
        open_result = MagicMock()
        open_result.all.return_value = []

        mock_db.execute.side_effect = [spec_result, open_result]

        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings()

        result = await svc.check_correlation(signal, settings, spec)
        assert result["result"] == "PASS"

    @pytest.mark.asyncio
    async def test_warn_one_correlated(self, svc, mock_db):
        """Warn with exactly 1 correlated open position."""
        # normalize_symbol for signal -> NQ
        spec_result1 = MagicMock()
        spec_result1.scalar_one_or_none.return_value = make_contract_spec(full_size_symbol="NQ")

        # Get open positions
        open_result = MagicMock()
        open_result.all.return_value = [("ES",)]

        # normalize_symbol for ES -> ES (no full_size_symbol)
        spec_result2 = MagicMock()
        spec_result2.scalar_one_or_none.return_value = make_contract_spec(
            symbol="ES", full_size_symbol=None
        )

        # Correlation lookup (sorted pair: ES, NQ)
        corr_obj = MagicMock(spec=InstrumentCorrelation)
        corr_obj.correlation = Decimal("0.85")
        corr_result = MagicMock()
        corr_result.scalar_one_or_none.return_value = corr_obj

        mock_db.execute.side_effect = [
            spec_result1, open_result, spec_result2, corr_result
        ]

        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(correlation_limit=0.70)

        result = await svc.check_correlation(signal, settings, spec)
        assert result["result"] == "WARN"
        assert result["actual_value"] == 1

    @pytest.mark.asyncio
    async def test_fail_two_correlated(self, svc, mock_db):
        """Fail with 2+ correlated open positions."""
        # normalize signal
        spec_result1 = MagicMock()
        spec_result1.scalar_one_or_none.return_value = make_contract_spec(full_size_symbol="NQ")

        # open positions
        open_result = MagicMock()
        open_result.all.return_value = [("ES",), ("YM",)]

        # normalize ES
        spec_es = MagicMock()
        spec_es.scalar_one_or_none.return_value = make_contract_spec(
            symbol="ES", full_size_symbol=None
        )
        # corr ES-NQ
        corr1 = MagicMock(spec=InstrumentCorrelation)
        corr1.correlation = Decimal("0.85")
        corr_result1 = MagicMock()
        corr_result1.scalar_one_or_none.return_value = corr1

        # normalize YM
        spec_ym = MagicMock()
        spec_ym.scalar_one_or_none.return_value = make_contract_spec(
            symbol="YM", full_size_symbol=None
        )
        # corr NQ-YM
        corr2 = MagicMock(spec=InstrumentCorrelation)
        corr2.correlation = Decimal("0.90")
        corr_result2 = MagicMock()
        corr_result2.scalar_one_or_none.return_value = corr2

        mock_db.execute.side_effect = [
            spec_result1, open_result,
            spec_es, corr_result1,
            spec_ym, corr_result2,
        ]

        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(correlation_limit=0.70)

        result = await svc.check_correlation(signal, settings, spec)
        assert result["result"] == "FAIL"
        assert result["actual_value"] == 2

    @pytest.mark.asyncio
    async def test_normalizes_micro_symbols(self, svc, mock_db):
        """MNQ treated as NQ for correlation lookups."""
        # normalize MNQ -> NQ
        spec_result = MagicMock()
        spec_mnq = make_contract_spec(symbol="MNQ", full_size_symbol="NQ")
        spec_result.scalar_one_or_none.return_value = spec_mnq

        mock_db.execute.return_value = spec_result

        normalized = await svc._normalize_symbol("MNQ")
        assert normalized == "NQ"


# ═══════════════════════════════════════════════════════════════════
# Trading Hours Tests
# ═══════════════════════════════════════════════════════════════════


class TestTradingHours:
    """Test trading hours check."""

    @pytest.mark.asyncio
    async def test_pass_rth_during_hours(self, svc, mock_db):
        """Pass when RTH mode and within 08:30-15:15 ET."""
        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(trading_hours_mode="RTH")

        # Mock datetime to be within RTH (e.g., 14:00 ET = 19:00 UTC)
        mock_now = datetime(2025, 1, 15, 19, 0, 0, tzinfo=UTC)
        with patch("app.services.risk_service.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = await svc.check_trading_hours(signal, settings, spec)

        assert result["result"] == "PASS"

    @pytest.mark.asyncio
    async def test_fail_rth_outside_hours(self, svc, mock_db):
        """Fail when RTH mode and outside trading hours."""
        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(trading_hours_mode="RTH")

        # 03:00 ET = 08:00 UTC (before 08:30 ET)
        mock_now = datetime(2025, 1, 15, 8, 0, 0, tzinfo=UTC)
        with patch("app.services.risk_service.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = await svc.check_trading_hours(signal, settings, spec)

        assert result["result"] == "FAIL"

    @pytest.mark.asyncio
    async def test_pass_24h_mode(self, svc, mock_db):
        """24H mode always passes."""
        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(trading_hours_mode="24H")

        result = await svc.check_trading_hours(signal, settings, spec)
        assert result["result"] == "PASS"


# ═══════════════════════════════════════════════════════════════════
# Circuit Breaker Tests
# ═══════════════════════════════════════════════════════════════════


class TestCircuitBreaker:
    """Test circuit breaker behavior."""

    @pytest.mark.asyncio
    async def test_record_loss_increments(self, svc, mock_redis, mock_db):
        """record_loss increments consecutive loss counter."""
        mock_redis.hincrby.return_value = 1

        # Mock get_risk_settings
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tripped = await svc.record_loss(_USER_ID)
        assert tripped is False
        mock_redis.hincrby.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_record_loss_trips(self, svc, mock_redis, mock_db):
        """record_loss trips circuit breaker at threshold."""
        mock_redis.hincrby.return_value = 3  # equals threshold

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tripped = await svc.record_loss(_USER_ID)
        assert tripped is True
        # Should have called trip_circuit_breaker -> hset
        mock_redis.hset.assert_awaited()

    @pytest.mark.asyncio
    async def test_record_win_resets(self, svc, mock_redis):
        """record_win resets consecutive losses to 0."""
        await svc.record_win(_USER_ID)
        mock_redis.hset.assert_awaited_once()
        call_args = mock_redis.hset.call_args
        assert call_args.args[1] == "consecutive_losses"
        assert call_args.args[2] == "0"

    @pytest.mark.asyncio
    async def test_trip_sets_state(self, svc, mock_redis):
        """trip_circuit_breaker sets state to TRIPPED."""
        await svc.trip_circuit_breaker(_USER_ID)
        mock_redis.hset.assert_awaited_once()
        mapping = mock_redis.hset.call_args.kwargs["mapping"]
        assert mapping["state"] == "TRIPPED"

    @pytest.mark.asyncio
    async def test_get_state_default_closed(self, svc, mock_redis, mock_db):
        """Default circuit breaker state is CLOSED."""
        mock_redis.hgetall.return_value = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        state = await svc.get_circuit_breaker_state(_USER_ID)
        assert state["state"] == "CLOSED"
        assert state["consecutive_losses"] == 0


# ═══════════════════════════════════════════════════════════════════
# Quantity Calculation Tests
# ═══════════════════════════════════════════════════════════════════


class TestQuantityCalculation:
    """Test risk-based quantity calculation."""

    @pytest.mark.asyncio
    async def test_calculate_quantity_risk_based(self, svc, mock_db):
        """Quantity = floor(max_risk / risk_per_contract), clamped to max size."""
        signal = make_signal(enrichment_data={"risk_per_contract": 40.0})
        spec = make_contract_spec(is_micro=True)
        # max_single_trade_risk=200, risk_per_contract=40 -> floor(200/40) = 5
        # max_position_size_micro=2 -> clamped to 2
        settings = default_settings(
            max_single_trade_risk=200.0,
            max_position_size_micro=2,
        )

        qty = await svc.calculate_quantity(signal, settings, spec)
        assert qty == 2

    @pytest.mark.asyncio
    async def test_calculate_quantity_unclamped(self, svc, mock_db):
        """Quantity not clamped when under max size."""
        signal = make_signal(enrichment_data={"risk_per_contract": 100.0})
        spec = make_contract_spec(is_micro=True)
        # max_risk=200 / rpc=100 = 2, max_size=5 -> 2
        settings = default_settings(
            max_single_trade_risk=200.0,
            max_position_size_micro=5,
        )

        qty = await svc.calculate_quantity(signal, settings, spec)
        assert qty == 2

    @pytest.mark.asyncio
    async def test_calculate_quantity_no_risk_defaults_to_1(self, svc, mock_db):
        """Default to 1 when risk_per_contract is missing."""
        signal = make_signal(enrichment_data={})
        spec = make_contract_spec()
        settings = default_settings()

        qty = await svc.calculate_quantity(signal, settings, spec)
        assert qty == 1

    @pytest.mark.asyncio
    async def test_calculate_quantity_minimum_1(self, svc, mock_db):
        """Quantity is always at least 1."""
        signal = make_signal(enrichment_data={"risk_per_contract": 500.0})
        spec = make_contract_spec(is_micro=True)
        # max_risk=200 / rpc=500 = floor(0.4) = 0 -> clamped to 1
        settings = default_settings(max_single_trade_risk=200.0)

        qty = await svc.calculate_quantity(signal, settings, spec)
        assert qty == 1
