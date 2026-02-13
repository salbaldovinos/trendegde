"""Unit tests for the execution service (bracket construction, fill processing, OCO, position management)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
import pytest_asyncio

from app.adapters.types import (
    BracketOrderResult,
    BracketRole,
    CancelResult,
    ModifyResult,
    OrderRequest,
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


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def make_signal(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "source": "MANUAL",
        "status": "ENRICHED",
        "instrument_symbol": "MNQ",
        "direction": "LONG",
        "entry_type": "MARKET",
        "entry_price": Decimal("18500.00"),
        "stop_loss_price": Decimal("18480.00"),
        "take_profit_price": Decimal("18540.00"),
        "quantity": 1,
        "enrichment_data": {"risk_per_contract": 10.0, "risk_reward_ratio": 2.0},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    signal = MagicMock(spec=Signal)
    for k, v in defaults.items():
        setattr(signal, k, v)
    return signal


def make_order(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "signal_id": uuid.uuid4(),
        "bracket_group_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "instrument_symbol": "MNQ",
        "side": "BUY",
        "order_type": "MARKET",
        "bracket_role": "ENTRY",
        "price": Decimal("18500.00"),
        "quantity": 1,
        "time_in_force": "GTC",
        "status": "CONSTRUCTED",
        "broker_order_id": None,
        "fill_price": None,
        "filled_quantity": None,
        "commission": None,
        "slippage_ticks": None,
        "submitted_at": None,
        "filled_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    order = MagicMock(spec=Order)
    for k, v in defaults.items():
        setattr(order, k, v)
    return order


def make_position(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "signal_id": uuid.uuid4(),
        "entry_order_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "instrument_symbol": "MNQ",
        "direction": "LONG",
        "entry_price": Decimal("18500.00"),
        "current_price": Decimal("18510.00"),
        "stop_loss_price": Decimal("18480.00"),
        "take_profit_price": Decimal("18540.00"),
        "quantity": 1,
        "unrealized_pnl": Decimal("100.00"),
        "realized_pnl": None,
        "net_pnl": None,
        "r_multiple": None,
        "mae": None,
        "mfe": None,
        "status": "OPEN",
        "exit_reason": None,
        "entered_at": datetime.now(UTC),
        "closed_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    position = MagicMock(spec=Position)
    for k, v in defaults.items():
        setattr(position, k, v)
    return position


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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest_asyncio.fixture
async def mock_redis():
    return AsyncMock()


@pytest_asyncio.fixture
async def svc(mock_db, mock_redis):
    return ExecutionService(mock_db, mock_redis)


# ═══════════════════════════════════════════════════════════════════
# Bracket Construction Tests
# ═══════════════════════════════════════════════════════════════════


class TestBracketConstruction:
    """Test bracket order construction from signals."""

    @pytest.mark.asyncio
    async def test_construct_bracket_long(self, svc, mock_db):
        """LONG signal creates BUY entry + SELL SL + SELL TP."""
        signal = make_signal(direction="LONG")
        bracket_id = await svc.construct_bracket_order(signal, quantity=1)

        assert bracket_id is not None
        # 3 orders added: entry + SL + TP
        assert mock_db.add.call_count == 3
        orders_added = [c.args[0] for c in mock_db.add.call_args_list]

        entry = orders_added[0]
        assert entry.side == "BUY"
        assert entry.bracket_role == "ENTRY"

        sl = orders_added[1]
        assert sl.side == "SELL"
        assert sl.bracket_role == "STOP_LOSS"
        assert sl.order_type == "STOP"

        tp = orders_added[2]
        assert tp.side == "SELL"
        assert tp.bracket_role == "TAKE_PROFIT"
        assert tp.order_type == "LIMIT"

    @pytest.mark.asyncio
    async def test_construct_bracket_short(self, svc, mock_db):
        """SHORT signal creates SELL entry + BUY SL + BUY TP."""
        signal = make_signal(direction="SHORT")
        bracket_id = await svc.construct_bracket_order(signal, quantity=2)

        orders_added = [c.args[0] for c in mock_db.add.call_args_list]

        entry = orders_added[0]
        assert entry.side == "SELL"
        assert entry.bracket_role == "ENTRY"
        assert entry.quantity == 2

        sl = orders_added[1]
        assert sl.side == "BUY"
        assert sl.bracket_role == "STOP_LOSS"

        tp = orders_added[2]
        assert tp.side == "BUY"
        assert tp.bracket_role == "TAKE_PROFIT"

    @pytest.mark.asyncio
    async def test_construct_bracket_no_sl(self, svc, mock_db):
        """Missing SL creates only entry + TP."""
        signal = make_signal(stop_loss_price=None)
        await svc.construct_bracket_order(signal, quantity=1)

        # entry + TP = 2 adds
        assert mock_db.add.call_count == 2
        roles = [c.args[0].bracket_role for c in mock_db.add.call_args_list]
        assert "ENTRY" in roles
        assert "TAKE_PROFIT" in roles
        assert "STOP_LOSS" not in roles

    @pytest.mark.asyncio
    async def test_construct_bracket_no_tp(self, svc, mock_db):
        """Missing TP creates only entry + SL."""
        signal = make_signal(take_profit_price=None)
        await svc.construct_bracket_order(signal, quantity=1)

        assert mock_db.add.call_count == 2
        roles = [c.args[0].bracket_role for c in mock_db.add.call_args_list]
        assert "ENTRY" in roles
        assert "STOP_LOSS" in roles
        assert "TAKE_PROFIT" not in roles

    @pytest.mark.asyncio
    async def test_construct_bracket_market_entry(self, svc, mock_db):
        """Market entry type produces MARKET order."""
        signal = make_signal(entry_type="MARKET")
        await svc.construct_bracket_order(signal, quantity=1)

        entry = mock_db.add.call_args_list[0].args[0]
        assert entry.order_type == "MARKET"

    @pytest.mark.asyncio
    async def test_construct_bracket_limit_entry(self, svc, mock_db):
        """Limit entry type produces LIMIT order."""
        signal = make_signal(entry_type="LIMIT")
        await svc.construct_bracket_order(signal, quantity=1)

        entry = mock_db.add.call_args_list[0].args[0]
        assert entry.order_type == "LIMIT"


# ═══════════════════════════════════════════════════════════════════
# Fill Processing Tests
# ═══════════════════════════════════════════════════════════════════


class TestFillProcessing:
    """Test fill processing for entry, stop loss, and take profit orders."""

    @pytest.mark.asyncio
    async def test_process_fill_entry(self, svc, mock_db):
        """Entry fill creates a position."""
        order = make_order(bracket_role="ENTRY", status="SUBMITTED")

        # Mock DB: return order on select, return signal for position creation
        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar_one_or_none.return_value = order
        mock_db.execute.return_value = mock_scalar_result

        signal = make_signal()
        # Second call for signal lookup in _create_position_from_fill
        mock_scalar_result2 = MagicMock()
        mock_scalar_result2.scalar_one_or_none.return_value = signal
        mock_db.execute.side_effect = [mock_scalar_result, mock_scalar_result2]

        await svc.process_fill(
            order.id, {"fill_price": 18500.25, "fill_quantity": 1}
        )

        assert order.status == "FILLED"
        assert order.fill_price == Decimal("18500.25")
        # A position was added
        position_adds = [
            c.args[0]
            for c in mock_db.add.call_args_list
            if isinstance(c.args[0], Position)
        ]
        assert len(position_adds) == 1

    @pytest.mark.asyncio
    async def test_process_fill_stop_loss(self, svc, mock_db):
        """SL fill closes position and triggers OCO cancel."""
        order = make_order(bracket_role="STOP_LOSS", status="SUBMITTED")

        # First call: return the order
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = order

        # Second call: return position for _close_position_from_fill
        position = make_position()
        mock_result2 = MagicMock()
        mock_scalars2 = MagicMock()
        mock_scalars2.first.return_value = position
        mock_result2.scalars.return_value = mock_scalars2

        # Third call: find contract spec
        spec = make_contract_spec()
        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none.return_value = spec

        # Fourth call: OCO - find pending orders
        partner = make_order(bracket_role="TAKE_PROFIT", status="SUBMITTED")
        mock_result4 = MagicMock()
        mock_scalars4 = MagicMock()
        mock_scalars4.all.return_value = [partner]
        mock_result4.scalars.return_value = mock_scalars4

        mock_db.execute.side_effect = [
            mock_result1, mock_result2, mock_result3, mock_result4
        ]

        await svc.process_fill(
            order.id, {"fill_price": 18480.00, "fill_quantity": 1}
        )

        assert order.status == "FILLED"
        assert partner.status == "CANCELLED"

    @pytest.mark.asyncio
    async def test_process_fill_take_profit(self, svc, mock_db):
        """TP fill closes position and triggers OCO cancel."""
        order = make_order(bracket_role="TAKE_PROFIT", status="SUBMITTED")

        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = order

        position = make_position()
        mock_result2 = MagicMock()
        mock_scalars2 = MagicMock()
        mock_scalars2.first.return_value = position
        mock_result2.scalars.return_value = mock_scalars2

        spec = make_contract_spec()
        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none.return_value = spec

        partner = make_order(bracket_role="STOP_LOSS", status="SUBMITTED")
        mock_result4 = MagicMock()
        mock_scalars4 = MagicMock()
        mock_scalars4.all.return_value = [partner]
        mock_result4.scalars.return_value = mock_scalars4

        mock_db.execute.side_effect = [
            mock_result1, mock_result2, mock_result3, mock_result4
        ]

        await svc.process_fill(
            order.id, {"fill_price": 18540.00, "fill_quantity": 1}
        )

        assert order.status == "FILLED"
        assert partner.status == "CANCELLED"


# ═══════════════════════════════════════════════════════════════════
# OCO Behavior Tests
# ═══════════════════════════════════════════════════════════════════


class TestOCOBehavior:
    """Test OCO (One-Cancels-Other) fill handling."""

    @pytest.mark.asyncio
    async def test_handle_oco_cancels_partner(self, svc, mock_db):
        """Cancels the other pending order in the bracket group."""
        partner = make_order(bracket_role="TAKE_PROFIT", status="SUBMITTED")
        filled_id = uuid.uuid4()
        bg_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [partner]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await svc.handle_oco_fill(filled_id, bg_id)

        assert partner.status == "CANCELLED"

    @pytest.mark.asyncio
    async def test_handle_oco_no_pending(self, svc, mock_db):
        """No error when there are no pending orders to cancel."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Should not raise
        await svc.handle_oco_fill(uuid.uuid4(), uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════
# Position Management Tests
# ═══════════════════════════════════════════════════════════════════


class TestPositionManagement:
    """Test close position, flatten, cancel, and modify operations."""

    @pytest.mark.asyncio
    async def test_close_position_not_found(self, svc, mock_db):
        """404 for missing position."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        adapter = AsyncMock()
        with pytest.raises(NotFoundError):
            await svc.close_position(uuid.uuid4(), uuid.uuid4(), adapter)

    @pytest.mark.asyncio
    async def test_cancel_order(self, svc, mock_db):
        """Cancels a SUBMITTED order."""
        order = make_order(
            status="SUBMITTED",
            broker_order_id="PAPER-123",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order
        mock_db.execute.return_value = mock_result

        adapter = AsyncMock()
        adapter.cancel_order.return_value = CancelResult(
            broker_order_id="PAPER-123", success=True
        )

        result = await svc.cancel_order(order.user_id, order.id, adapter)

        assert order.status == "CANCELLED"
        adapter.cancel_order.assert_awaited_once_with("PAPER-123")

    @pytest.mark.asyncio
    async def test_cancel_order_wrong_status(self, svc, mock_db):
        """ConflictError for FILLED order."""
        order = make_order(status="FILLED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order
        mock_db.execute.return_value = mock_result

        adapter = AsyncMock()
        with pytest.raises(ConflictError, match="Cannot cancel"):
            await svc.cancel_order(order.user_id, order.id, adapter)

    @pytest.mark.asyncio
    async def test_modify_order(self, svc, mock_db):
        """Modifies price and quantity of a pending order."""
        order = make_order(
            status="SUBMITTED",
            broker_order_id="PAPER-123",
            price=Decimal("18500.00"),
            quantity=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order
        mock_db.execute.return_value = mock_result

        adapter = AsyncMock()
        adapter.modify_order.return_value = ModifyResult(
            broker_order_id="PAPER-123",
            success=True,
            new_price=Decimal("18510.00"),
        )

        result = await svc.modify_order(
            order.user_id,
            order.id,
            {"new_price": 18510.00, "new_quantity": 2},
            adapter,
        )

        assert order.price == Decimal("18510.0")
        assert order.quantity == 2


# ═══════════════════════════════════════════════════════════════════
# Finalization / P&L Tests
# ═══════════════════════════════════════════════════════════════════


class TestFinalization:
    """Test position finalization with P&L and R-multiple calculation."""

    @pytest.mark.asyncio
    async def test_finalize_long_profit(self, svc, mock_db):
        """Long position closed at profit."""
        position = make_position(
            direction="LONG",
            entry_price=Decimal("18500.00"),
            stop_loss_price=Decimal("18480.00"),
            quantity=1,
        )
        spec = make_contract_spec(tick_size=Decimal("0.25"), tick_value=Decimal("0.50"))
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = spec
        mock_db.execute.return_value = mock_result

        await svc._finalize_position(position, 18520.0, "MANUAL")

        # P&L = (18520 - 18500) / 0.25 * 0.50 * 1 = 80 ticks * 0.50 = 40.0
        assert position.status == "CLOSED"
        assert float(position.realized_pnl) == 40.0
        assert float(position.net_pnl) == 40.0
        assert position.exit_reason == "MANUAL"

    @pytest.mark.asyncio
    async def test_finalize_long_loss(self, svc, mock_db):
        """Long position closed at loss."""
        position = make_position(
            direction="LONG",
            entry_price=Decimal("18500.00"),
            stop_loss_price=Decimal("18480.00"),
            quantity=1,
        )
        spec = make_contract_spec(tick_size=Decimal("0.25"), tick_value=Decimal("0.50"))
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = spec
        mock_db.execute.return_value = mock_result

        await svc._finalize_position(position, 18480.0, "STOP_LOSS")

        # P&L = (18480 - 18500) / 0.25 * 0.50 * 1 = -80 ticks * 0.50 = -40.0
        assert float(position.realized_pnl) == -40.0
        assert position.status == "CLOSED"

    @pytest.mark.asyncio
    async def test_finalize_short_profit(self, svc, mock_db):
        """Short position closed at profit."""
        position = make_position(
            direction="SHORT",
            entry_price=Decimal("18500.00"),
            stop_loss_price=Decimal("18520.00"),
            quantity=1,
        )
        spec = make_contract_spec(tick_size=Decimal("0.25"), tick_value=Decimal("0.50"))
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = spec
        mock_db.execute.return_value = mock_result

        await svc._finalize_position(position, 18480.0, "TAKE_PROFIT")

        # P&L = (18500 - 18480) / 0.25 * 0.50 * 1 = 80 ticks * 0.50 = 40.0
        assert float(position.realized_pnl) == 40.0

    @pytest.mark.asyncio
    async def test_finalize_r_multiple(self, svc, mock_db):
        """R-multiple calculated correctly with stop loss."""
        position = make_position(
            direction="LONG",
            entry_price=Decimal("18500.00"),
            stop_loss_price=Decimal("18480.00"),
            quantity=1,
        )
        spec = make_contract_spec(tick_size=Decimal("0.25"), tick_value=Decimal("0.50"))
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = spec
        mock_db.execute.return_value = mock_result

        await svc._finalize_position(position, 18540.0, "TAKE_PROFIT")

        # Risk = |18500 - 18480| / 0.25 * 0.50 * 1 = 80 * 0.50 = 40.0
        # P&L = (18540 - 18500) / 0.25 * 0.50 * 1 = 160 * 0.50 = 80.0
        # R = 80.0 / 40.0 = 2.0
        assert float(position.r_multiple) == 2.0

    @pytest.mark.asyncio
    async def test_finalize_uses_contract_spec(self, svc, mock_db):
        """Uses DB contract spec for tick calculations, not defaults."""
        position = make_position(
            direction="LONG",
            entry_price=Decimal("5000.00"),
            stop_loss_price=Decimal("4990.00"),
            instrument_symbol="ES",
            quantity=1,
        )
        # ES has different tick_size/tick_value than default
        spec = make_contract_spec(
            symbol="ES",
            tick_size=Decimal("0.25"),
            tick_value=Decimal("12.50"),
            is_micro=False,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = spec
        mock_db.execute.return_value = mock_result

        await svc._finalize_position(position, 5020.0, "MANUAL")

        # P&L = (5020 - 5000) / 0.25 * 12.50 * 1 = 80 * 12.50 = 1000.0
        assert float(position.realized_pnl) == 1000.0


# ═══════════════════════════════════════════════════════════════════
# OrderEvent Recording Tests
# ═══════════════════════════════════════════════════════════════════


class TestOrderEventRecording:
    """Test OrderEvent audit trail creation."""

    @pytest.mark.asyncio
    async def test_record_order_event(self, svc, mock_db):
        """Creates an OrderEvent record with correct fields."""
        order_id = uuid.uuid4()
        await svc._record_order_event(
            order_id, "CONSTRUCTED", "SUBMITTED",
            fill_price=Decimal("18500.00"),
            fill_qty=1,
            reason="Test submission",
        )

        mock_db.add.assert_called_once()
        event = mock_db.add.call_args.args[0]
        assert isinstance(event, OrderEvent)
        assert event.order_id == order_id
        assert event.previous_state == "CONSTRUCTED"
        assert event.new_state == "SUBMITTED"
        assert event.fill_price == Decimal("18500.00")
        assert event.fill_quantity == 1
        assert event.reason == "Test submission"

    @pytest.mark.asyncio
    async def test_submit_records_events(self, svc, mock_db):
        """submit_bracket_order creates OrderEvent records for state transitions."""
        user_id = uuid.uuid4()
        bg_id = uuid.uuid4()

        entry = make_order(
            bracket_group_id=bg_id, bracket_role="ENTRY",
            side="BUY", order_type="MARKET", user_id=user_id,
        )
        sl = make_order(
            bracket_group_id=bg_id, bracket_role="STOP_LOSS",
            side="SELL", order_type="STOP", user_id=user_id,
        )
        tp = make_order(
            bracket_group_id=bg_id, bracket_role="TAKE_PROFIT",
            side="SELL", order_type="LIMIT", user_id=user_id,
        )

        # Mock DB to return our orders
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [entry, sl, tp]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Mock adapter
        adapter = AsyncMock()
        now = datetime.now(UTC)
        adapter.place_bracket_order.return_value = BracketOrderResult(
            entry=OrderResult(
                broker_order_id="PAPER-E1", status="FILLED",
                fill_price=Decimal("18500.25"), fill_quantity=1,
                commission=Decimal("0.62"), timestamp=now,
            ),
            stop_loss=OrderResult(
                broker_order_id="PAPER-SL1", status="SUBMITTED",
                timestamp=now,
            ),
            take_profit=OrderResult(
                broker_order_id="PAPER-TP1", status="SUBMITTED",
                timestamp=now,
            ),
        )

        # Also mock the signal lookup for position creation
        signal = make_signal(user_id=user_id)
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = signal
        mock_db.execute.side_effect = [mock_result, mock_result2]

        result = await svc.submit_bracket_order(
            user_id, str(bg_id), adapter
        )

        # Verify order events were recorded (add calls include OrderEvent instances)
        event_adds = [
            c.args[0]
            for c in mock_db.add.call_args_list
            if isinstance(c.args[0], OrderEvent)
        ]
        # Entry: CONSTRUCTED->FILLED (2 events: CONSTRUCTED->FILLED, SUBMITTED->FILLED)
        # SL: CONSTRUCTED->SUBMITTED
        # TP: CONSTRUCTED->SUBMITTED
        assert len(event_adds) >= 3
