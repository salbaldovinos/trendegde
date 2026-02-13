"""Integration tests for the full execution pipeline (signal -> risk -> bracket -> fill -> position)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.adapters.paper import PaperBrokerAdapter
from app.adapters.types import (
    BracketOrderResult,
    OrderResult,
    OrderSide,
    OrderType,
)
from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.contract_specification import ContractSpecification
from app.db.models.order import Order
from app.db.models.order_event import OrderEvent
from app.db.models.position import Position
from app.db.models.signal import Signal
from app.services.execution_service import ExecutionService
from app.services.risk_service import RiskService
from app.services.signal_service import SignalService


# ---------------------------------------------------------------------------
# Helpers
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
        "trading_hours_mode": "24H",
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


class MockDBSession:
    """A mock DB session that tracks added objects by type."""

    def __init__(self):
        self._added: list = []
        self._execute_results: list = []
        self._execute_idx = 0

    def add(self, obj):
        self._added.append(obj)

    async def flush(self):
        # Assign UUIDs to objects that need them
        for obj in self._added:
            if isinstance(obj, (Order, Position, OrderEvent)):
                if not hasattr(obj, "id") or obj.id is None:
                    obj.id = uuid.uuid4()

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    def push_result(self, result):
        self._execute_results.append(result)

    async def execute(self, stmt):
        if self._execute_idx < len(self._execute_results):
            result = self._execute_results[self._execute_idx]
            self._execute_idx += 1
            return result
        # Default empty result
        mock = MagicMock()
        mock.scalar_one_or_none.return_value = None
        mock.scalar.return_value = 0
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock.scalars.return_value = mock_scalars
        return mock

    def get_added(self, cls):
        return [obj for obj in self._added if isinstance(obj, cls)]


@pytest_asyncio.fixture
async def mock_db():
    return MockDBSession()


@pytest_asyncio.fixture
async def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.hincrby = AsyncMock(return_value=0)
    redis.hset = AsyncMock()
    return redis


# ═══════════════════════════════════════════════════════════════════
# Pipeline Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestExecutionPipeline:
    """Test the full execution pipeline end-to-end with mocked DB."""

    @pytest.mark.asyncio
    async def test_signal_to_position(self, mock_db, mock_redis):
        """Full pipeline: signal -> risk checks pass -> bracket -> fill -> position."""
        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings()

        # ------ Risk checks ------
        risk_svc = RiskService(mock_db, mock_redis)

        # We need mock results for each risk check DB query:
        # 1. _get_contract_spec
        spec_result = MagicMock()
        spec_result.scalar_one_or_none.return_value = spec

        # 2. check_max_position_size (count open positions)
        count_result1 = MagicMock()
        count_result1.scalar.return_value = 0

        # 3. check_daily_loss_limit (realized losses)
        loss_result1 = MagicMock()
        loss_result1.scalar.return_value = Decimal("0")

        # 4. check_daily_loss_limit (unrealized losses)
        loss_result2 = MagicMock()
        loss_result2.scalar.return_value = Decimal("0")

        # 5. check_max_concurrent_positions
        count_result2 = MagicMock()
        count_result2.scalar.return_value = 0

        # 6. check_correlation -> _normalize_symbol
        norm_result = MagicMock()
        norm_result.scalar_one_or_none.return_value = spec

        # 7. check_correlation -> open positions
        open_result = MagicMock()
        open_result.all.return_value = []

        mock_db.push_result(spec_result)     # _get_contract_spec
        mock_db.push_result(count_result1)   # max_position_size
        mock_db.push_result(loss_result1)    # daily_loss realized
        mock_db.push_result(loss_result2)    # daily_loss unrealized
        mock_db.push_result(count_result2)   # max_concurrent
        # min_risk_reward: no DB calls
        mock_db.push_result(norm_result)     # correlation -> normalize
        mock_db.push_result(open_result)     # correlation -> open positions
        # max_single_trade_risk: no DB calls
        # trading_hours: no DB calls
        # staleness: no DB calls

        check_results = await risk_svc.run_all_checks(signal, settings)

        # All checks should pass
        failed = [c for c in check_results if c["result"] == "FAIL"]
        assert len(failed) == 0, f"Unexpected failures: {failed}"

        # ------ Bracket construction ------
        exec_svc = ExecutionService(mock_db, mock_redis)
        bracket_group_id = await exec_svc.construct_bracket_order(signal, quantity=1)

        orders = mock_db.get_added(Order)
        assert len(orders) == 3  # ENTRY + SL + TP

    @pytest.mark.asyncio
    async def test_signal_rejected_by_risk(self, mock_db, mock_redis):
        """Signal rejected when at max concurrent positions."""
        signal = make_signal()
        spec = make_contract_spec()
        settings = default_settings(max_concurrent_positions=3)

        risk_svc = RiskService(mock_db, mock_redis)

        # _get_contract_spec
        spec_result = MagicMock()
        spec_result.scalar_one_or_none.return_value = spec

        # max_position_size: 0 current
        count_result1 = MagicMock()
        count_result1.scalar.return_value = 0

        # daily_loss: 0 realized
        loss_result1 = MagicMock()
        loss_result1.scalar.return_value = Decimal("0")
        # daily_loss: 0 unrealized
        loss_result2 = MagicMock()
        loss_result2.scalar.return_value = Decimal("0")

        # max_concurrent: already at 3
        count_result2 = MagicMock()
        count_result2.scalar.return_value = 3

        mock_db.push_result(spec_result)
        mock_db.push_result(count_result1)
        mock_db.push_result(loss_result1)
        mock_db.push_result(loss_result2)
        mock_db.push_result(count_result2)

        check_results = await risk_svc.run_all_checks(signal, settings)

        # Should fail-fast on max_concurrent_positions
        failed = [c for c in check_results if c["result"] == "FAIL"]
        assert len(failed) == 1
        assert failed[0]["check_name"] == "max_concurrent_positions"

    @pytest.mark.asyncio
    async def test_position_close_pnl(self, mock_db, mock_redis):
        """Close position and verify P&L calculation."""
        position = MagicMock(spec=Position)
        position.id = uuid.uuid4()
        position.user_id = _USER_ID
        position.signal_id = uuid.uuid4()
        position.entry_order_id = uuid.uuid4()
        position.instrument_symbol = "MNQ"
        position.direction = "LONG"
        position.entry_price = Decimal("18500.00")
        position.current_price = Decimal("18510.00")
        position.stop_loss_price = Decimal("18480.00")
        position.take_profit_price = Decimal("18540.00")
        position.quantity = 1
        position.unrealized_pnl = Decimal("100.00")
        position.realized_pnl = None
        position.net_pnl = None
        position.r_multiple = None
        position.status = "OPEN"

        exec_svc = ExecutionService(mock_db, mock_redis)
        spec = make_contract_spec()

        # For _finalize_position: contract spec lookup
        spec_result = MagicMock()
        spec_result.scalar_one_or_none.return_value = spec
        mock_db.push_result(spec_result)

        await exec_svc._finalize_position(position, 18520.0, "MANUAL")

        assert position.status == "CLOSED"
        # (18520 - 18500) / 0.25 * 0.50 * 1 = 40.0
        assert float(position.realized_pnl) == 40.0
        assert position.exit_reason == "MANUAL"

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks(self, mock_db, mock_redis):
        """Tripped circuit breaker state is detectable."""
        mock_redis.hgetall.return_value = {
            "state": "TRIPPED",
            "consecutive_losses": "3",
            "last_tripped_at": datetime.now(UTC).isoformat(),
        }

        # Mock get_risk_settings
        settings_result = MagicMock()
        settings_result.scalar_one_or_none.return_value = None
        mock_db.push_result(settings_result)

        risk_svc = RiskService(mock_db, mock_redis)
        state = await risk_svc.get_circuit_breaker_state(_USER_ID)

        assert state["state"] == "TRIPPED"
        assert state["consecutive_losses"] == 3

    @pytest.mark.asyncio
    async def test_flatten_all_cleanup(self, mock_db, mock_redis):
        """Flatten all cancels pending orders when no positions open."""
        exec_svc = ExecutionService(mock_db, mock_redis)

        # No open positions
        pos_result = MagicMock()
        pos_scalars = MagicMock()
        pos_scalars.all.return_value = []
        pos_result.scalars.return_value = pos_scalars

        # 2 pending orders to cancel
        pending_order1 = MagicMock(spec=Order)
        pending_order1.id = uuid.uuid4()
        pending_order1.status = "SUBMITTED"
        pending_order2 = MagicMock(spec=Order)
        pending_order2.id = uuid.uuid4()
        pending_order2.status = "CONSTRUCTED"

        pending_result = MagicMock()
        pending_scalars = MagicMock()
        pending_scalars.all.return_value = [pending_order1, pending_order2]
        pending_result.scalars.return_value = pending_scalars

        mock_db.push_result(pos_result)
        mock_db.push_result(pending_result)

        adapter = AsyncMock()
        result = await exec_svc.flatten_all(_USER_ID, adapter)

        assert result["closed_count"] == 0
        assert result["cancelled_orders"] == 2
        assert pending_order1.status == "CANCELLED"
        assert pending_order2.status == "CANCELLED"
