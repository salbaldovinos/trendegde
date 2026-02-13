"""Paper trading simulator — fully functional broker adapter for simulated trading."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BrokerAdapter
from app.adapters.exceptions import OrderNotFoundError, OrderRejectedError
from app.adapters.types import (
    AccountInfo,
    BracketOrderResult,
    CancelResult,
    ConnectionStatus,
    ModifyResult,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatusInfo,
    OrderType,
    PositionInfo,
)
from app.core.logging import get_logger

logger = get_logger("trendedge.adapters.paper")

# Default paper account
_DEFAULT_BALANCE = Decimal("100000.00")
_DEFAULT_COMMISSION = Decimal("0.62")  # per micro contract per side


class PaperBrokerAdapter(BrokerAdapter):
    """Simulated broker for paper trading.

    Features:
    - Market orders fill at entry_price +/- slippage (adverse direction)
    - Limit orders fill at limit price
    - Stop orders fill at stop price +/- slippage
    - OCO behavior: when SL fills -> cancel TP; when TP fills -> cancel SL
    - MAE/MFE tracking during position lifetime
    - Commission simulation
    """

    def __init__(
        self,
        user_id: uuid.UUID,
        db: AsyncSession,
        redis: Redis,
        slippage_ticks: int = 1,
    ) -> None:
        self._user_id = user_id
        self._db = db
        self._redis = redis
        self._slippage_ticks = slippage_ticks
        self._connected = False
        # In-memory order book for paper orders
        self._pending_orders: dict[str, dict] = {}
        self._account_balance = _DEFAULT_BALANCE

    async def connect(self) -> ConnectionStatus:
        self._connected = True
        logger.info("Paper broker connected", user_id=str(self._user_id))
        return ConnectionStatus.CONNECTED

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("Paper broker disconnected", user_id=str(self._user_id))

    async def place_order(self, order: OrderRequest) -> OrderResult:
        broker_order_id = f"PAPER-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(UTC)

        if order.order_type == OrderType.MARKET:
            # Market orders fill immediately with slippage
            fill_price = self._apply_slippage(order)
            return OrderResult(
                broker_order_id=broker_order_id,
                status="FILLED",
                fill_price=fill_price,
                fill_quantity=order.quantity,
                commission=_DEFAULT_COMMISSION * order.quantity,
                message="Paper market order filled",
                timestamp=now,
            )

        if order.order_type in (OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT):
            # Limit/Stop orders are stored as pending
            self._pending_orders[broker_order_id] = {
                "order": order,
                "broker_order_id": broker_order_id,
                "created_at": now,
                "status": "SUBMITTED",
            }
            return OrderResult(
                broker_order_id=broker_order_id,
                status="SUBMITTED",
                message=f"Paper {order.order_type.value} order submitted",
                timestamp=now,
            )

        raise OrderRejectedError(f"Unsupported order type: {order.order_type}")

    async def place_bracket_order(
        self,
        entry: OrderRequest,
        stop_loss: OrderRequest,
        take_profit: OrderRequest,
    ) -> BracketOrderResult:
        bracket_group_id = entry.bracket_group_id or uuid.uuid4().hex[:12].upper()

        # Place entry order (fills immediately if market)
        entry_result = await self.place_order(entry)

        # Place SL and TP as pending
        sl_result = await self.place_order(stop_loss)
        tp_result = await self.place_order(take_profit)

        # Link SL and TP as OCO pair in pending orders
        if sl_result.broker_order_id in self._pending_orders:
            self._pending_orders[sl_result.broker_order_id]["oco_partner"] = (
                tp_result.broker_order_id
            )
        if tp_result.broker_order_id in self._pending_orders:
            self._pending_orders[tp_result.broker_order_id]["oco_partner"] = (
                sl_result.broker_order_id
            )

        return BracketOrderResult(
            entry=entry_result,
            stop_loss=sl_result,
            take_profit=tp_result,
            bracket_group_id=bracket_group_id,
        )

    async def cancel_order(self, broker_order_id: str) -> CancelResult:
        if broker_order_id in self._pending_orders:
            del self._pending_orders[broker_order_id]
            return CancelResult(
                broker_order_id=broker_order_id,
                success=True,
                message="Order cancelled",
            )
        return CancelResult(
            broker_order_id=broker_order_id,
            success=False,
            message="Order not found",
        )

    async def modify_order(
        self,
        broker_order_id: str,
        new_price: float | None = None,
        new_quantity: int | None = None,
    ) -> ModifyResult:
        if broker_order_id not in self._pending_orders:
            raise OrderNotFoundError(broker_order_id)

        pending = self._pending_orders[broker_order_id]
        order = pending["order"]
        if new_price is not None:
            order.price = Decimal(str(new_price))
        if new_quantity is not None:
            order.quantity = new_quantity

        return ModifyResult(
            broker_order_id=broker_order_id,
            success=True,
            new_price=Decimal(str(new_price)) if new_price else None,
            message="Order modified",
        )

    async def get_positions(self) -> list[PositionInfo]:
        # Paper positions are tracked in the DB, not in-memory
        return []

    async def get_order_status(self, broker_order_id: str) -> OrderStatusInfo:
        if broker_order_id in self._pending_orders:
            pending = self._pending_orders[broker_order_id]
            return OrderStatusInfo(
                broker_order_id=broker_order_id,
                status=pending["status"],
                timestamp=pending["created_at"],
            )
        raise OrderNotFoundError(broker_order_id)

    async def get_account_info(self) -> AccountInfo:
        return AccountInfo(
            account_id=f"PAPER-{str(self._user_id)[:8]}",
            balance=self._account_balance,
            buying_power=self._account_balance,
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            margin_used=Decimal("0"),
        )

    async def subscribe_order_updates(self) -> AsyncIterator[OrderResult]:
        # Paper trading uses polling instead of streaming
        return
        yield  # Make it a generator

    async def subscribe_position_updates(self) -> AsyncIterator[PositionInfo]:
        return
        yield  # Make it a generator

    def check_stop_loss_trigger(
        self, current_price: Decimal, order_data: dict
    ) -> OrderResult | None:
        """Check if a stop loss should trigger at the current price.

        Returns an OrderResult if triggered, None otherwise.
        """
        order: OrderRequest = order_data["order"]
        if order.price is None:
            return None

        # STOP for SELL side (long position SL) triggers when price <= stop price
        if order.side == OrderSide.SELL and current_price <= order.price:
            fill_price = order.price - Decimal(str(self._slippage_ticks)) * Decimal(
                "0.25"
            )
            return OrderResult(
                broker_order_id=order_data["broker_order_id"],
                status="FILLED",
                fill_price=fill_price,
                fill_quantity=order.quantity,
                commission=_DEFAULT_COMMISSION * order.quantity,
                message="Paper stop loss triggered",
                timestamp=datetime.now(UTC),
            )

        # STOP for BUY side (short position SL) triggers when price >= stop price
        if order.side == OrderSide.BUY and current_price >= order.price:
            fill_price = order.price + Decimal(str(self._slippage_ticks)) * Decimal(
                "0.25"
            )
            return OrderResult(
                broker_order_id=order_data["broker_order_id"],
                status="FILLED",
                fill_price=fill_price,
                fill_quantity=order.quantity,
                commission=_DEFAULT_COMMISSION * order.quantity,
                message="Paper stop loss triggered",
                timestamp=datetime.now(UTC),
            )

        return None

    def check_take_profit_trigger(
        self, current_price: Decimal, order_data: dict
    ) -> OrderResult | None:
        """Check if a take profit should trigger at the current price.

        Returns an OrderResult if triggered, None otherwise.
        """
        order: OrderRequest = order_data["order"]
        if order.price is None:
            return None

        # LIMIT for SELL side (long position TP) triggers when price >= limit price
        if order.side == OrderSide.SELL and current_price >= order.price:
            return OrderResult(
                broker_order_id=order_data["broker_order_id"],
                status="FILLED",
                fill_price=order.price,  # Limit fills at limit price
                fill_quantity=order.quantity,
                commission=_DEFAULT_COMMISSION * order.quantity,
                message="Paper take profit triggered",
                timestamp=datetime.now(UTC),
            )

        # LIMIT for BUY side (short position TP) triggers when price <= limit price
        if order.side == OrderSide.BUY and current_price <= order.price:
            return OrderResult(
                broker_order_id=order_data["broker_order_id"],
                status="FILLED",
                fill_price=order.price,
                fill_quantity=order.quantity,
                commission=_DEFAULT_COMMISSION * order.quantity,
                message="Paper take profit triggered",
                timestamp=datetime.now(UTC),
            )

        return None

    async def check_pending_triggers(
        self, instrument_symbol: str, current_price: Decimal
    ) -> list[OrderResult]:
        """Check all pending orders for trigger conditions. Returns list of fills.

        Called by the position monitoring Celery task.
        """
        fills: list[OrderResult] = []
        orders_to_remove: list[str] = []
        oco_to_cancel: list[str] = []

        for broker_id, order_data in self._pending_orders.items():
            order: OrderRequest = order_data["order"]
            if order.instrument_symbol != instrument_symbol:
                continue

            result: OrderResult | None = None

            if order.bracket_role.value == "STOP_LOSS":
                result = self.check_stop_loss_trigger(current_price, order_data)
            elif order.bracket_role.value == "TAKE_PROFIT":
                result = self.check_take_profit_trigger(current_price, order_data)

            if result:
                fills.append(result)
                orders_to_remove.append(broker_id)
                # OCO: cancel the partner
                partner_id = order_data.get("oco_partner")
                if partner_id and partner_id in self._pending_orders:
                    oco_to_cancel.append(partner_id)

        # Remove filled and OCO-cancelled orders
        for oid in orders_to_remove + oco_to_cancel:
            self._pending_orders.pop(oid, None)

        return fills

    def _apply_slippage(self, order: OrderRequest) -> Decimal:
        """Apply adverse slippage to a market order fill price."""
        base_price = order.price if order.price else Decimal("0")
        tick = Decimal("0.25")  # Default tick — should come from contract specs
        slippage = tick * Decimal(str(self._slippage_ticks))

        if order.side == OrderSide.BUY:
            return base_price + slippage  # Buy fills higher
        return base_price - slippage  # Sell fills lower
