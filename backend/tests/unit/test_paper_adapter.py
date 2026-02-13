"""Unit tests for the paper broker adapter (simulated trading)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.adapters.exceptions import OrderNotFoundError
from app.adapters.paper import PaperBrokerAdapter
from app.adapters.types import (
    BracketRole,
    OrderRequest,
    OrderSide,
    OrderType,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def adapter():
    user_id = uuid.uuid4()
    db = AsyncMock()
    redis = AsyncMock()
    adpt = PaperBrokerAdapter(
        user_id=user_id, db=db, redis=redis, slippage_ticks=1
    )
    await adpt.connect()
    return adpt


def make_order_request(**overrides):
    defaults = {
        "instrument_symbol": "MNQ",
        "side": OrderSide.BUY,
        "order_type": OrderType.MARKET,
        "quantity": 1,
        "price": Decimal("18500.00"),
        "bracket_role": BracketRole.ENTRY,
        "bracket_group_id": "test-bracket",
    }
    defaults.update(overrides)
    return OrderRequest(**defaults)


# ═══════════════════════════════════════════════════════════════════
# Paper Orders Tests
# ═══════════════════════════════════════════════════════════════════


class TestPaperOrders:
    """Test individual paper order placement and management."""

    @pytest.mark.asyncio
    async def test_market_order_fills_immediately(self, adapter):
        """Market order fills with status FILLED."""
        req = make_order_request(order_type=OrderType.MARKET)
        result = await adapter.place_order(req)

        assert result.status == "FILLED"
        assert result.fill_price is not None
        assert result.fill_quantity == 1
        assert result.commission is not None
        assert result.broker_order_id.startswith("PAPER-")

    @pytest.mark.asyncio
    async def test_market_order_slippage_buy(self, adapter):
        """Buy market order fills higher due to adverse slippage."""
        req = make_order_request(
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=Decimal("18500.00"),
        )
        result = await adapter.place_order(req)

        # Slippage = 1 tick * 0.25 = 0.25
        assert result.fill_price == Decimal("18500.25")

    @pytest.mark.asyncio
    async def test_market_order_slippage_sell(self, adapter):
        """Sell market order fills lower due to adverse slippage."""
        req = make_order_request(
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            price=Decimal("18500.00"),
        )
        result = await adapter.place_order(req)

        # Slippage = 1 tick * 0.25 = 0.25 (adverse for sell = lower)
        assert result.fill_price == Decimal("18499.75")

    @pytest.mark.asyncio
    async def test_limit_order_pending(self, adapter):
        """Limit order goes to SUBMITTED (pending) status."""
        req = make_order_request(
            order_type=OrderType.LIMIT,
            price=Decimal("18490.00"),
        )
        result = await adapter.place_order(req)

        assert result.status == "SUBMITTED"
        assert result.fill_price is None
        assert result.broker_order_id in adapter._pending_orders

    @pytest.mark.asyncio
    async def test_stop_order_pending(self, adapter):
        """Stop order goes to SUBMITTED (pending) status."""
        req = make_order_request(
            order_type=OrderType.STOP,
            price=Decimal("18480.00"),
        )
        result = await adapter.place_order(req)

        assert result.status == "SUBMITTED"
        assert result.broker_order_id in adapter._pending_orders

    @pytest.mark.asyncio
    async def test_cancel_pending_order(self, adapter):
        """Cancel a pending limit order."""
        req = make_order_request(
            order_type=OrderType.LIMIT,
            price=Decimal("18490.00"),
        )
        result = await adapter.place_order(req)
        broker_id = result.broker_order_id

        cancel = await adapter.cancel_order(broker_id)
        assert cancel.success is True
        assert broker_id not in adapter._pending_orders

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, adapter):
        """Cancel a nonexistent order returns success=False."""
        cancel = await adapter.cancel_order("PAPER-DOESNOTEXIST")
        assert cancel.success is False


# ═══════════════════════════════════════════════════════════════════
# Paper Bracket Tests
# ═══════════════════════════════════════════════════════════════════


class TestPaperBracket:
    """Test bracket order placement and OCO linking."""

    @pytest.mark.asyncio
    async def test_bracket_order_fills_entry(self, adapter):
        """Bracket order fills entry immediately (market), SL/TP go pending."""
        entry = make_order_request(
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=Decimal("18500.00"),
            bracket_role=BracketRole.ENTRY,
        )
        sl = make_order_request(
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            price=Decimal("18480.00"),
            bracket_role=BracketRole.STOP_LOSS,
        )
        tp = make_order_request(
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("18540.00"),
            bracket_role=BracketRole.TAKE_PROFIT,
        )

        result = await adapter.place_bracket_order(entry, sl, tp)

        assert result.entry.status == "FILLED"
        assert result.stop_loss.status == "SUBMITTED"
        assert result.take_profit.status == "SUBMITTED"
        assert result.entry.fill_price is not None

    @pytest.mark.asyncio
    async def test_bracket_oco_links(self, adapter):
        """SL and TP are linked as OCO partners."""
        entry = make_order_request(
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=Decimal("18500.00"),
            bracket_role=BracketRole.ENTRY,
        )
        sl = make_order_request(
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            price=Decimal("18480.00"),
            bracket_role=BracketRole.STOP_LOSS,
        )
        tp = make_order_request(
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("18540.00"),
            bracket_role=BracketRole.TAKE_PROFIT,
        )

        result = await adapter.place_bracket_order(entry, sl, tp)

        sl_id = result.stop_loss.broker_order_id
        tp_id = result.take_profit.broker_order_id

        # Verify OCO linking
        assert adapter._pending_orders[sl_id]["oco_partner"] == tp_id
        assert adapter._pending_orders[tp_id]["oco_partner"] == sl_id

    @pytest.mark.asyncio
    async def test_modify_pending_order(self, adapter):
        """Modify a pending order's price."""
        req = make_order_request(
            order_type=OrderType.LIMIT,
            price=Decimal("18490.00"),
        )
        result = await adapter.place_order(req)
        broker_id = result.broker_order_id

        mod = await adapter.modify_order(broker_id, new_price=18495.00)
        assert mod.success is True
        assert adapter._pending_orders[broker_id]["order"].price == Decimal("18495.0")

    @pytest.mark.asyncio
    async def test_modify_nonexistent_raises(self, adapter):
        """Modifying a nonexistent order raises OrderNotFoundError."""
        with pytest.raises(OrderNotFoundError):
            await adapter.modify_order("PAPER-DOESNOTEXIST", new_price=18495.00)
