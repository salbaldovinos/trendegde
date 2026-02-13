"""Trade execution: bracket construction, submission, fill handling, position management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BrokerAdapter
from app.adapters.types import (
    BracketRole,
    OrderRequest,
    OrderSide,
    OrderType,
)
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.db.models.contract_specification import ContractSpecification
from app.db.models.order import Order
from app.db.models.order_event import OrderEvent
from app.db.models.position import Position
from app.db.models.signal import Signal

logger = get_logger("trendedge.execution_service")


class ExecutionService:
    """Bracket order construction, submission, fill handling, and position lifecycle."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None) -> None:
        self._db = db
        self._redis = redis

    # ------------------------------------------------------------------
    # OrderEvent audit trail
    # ------------------------------------------------------------------

    async def _record_order_event(
        self,
        order_id: uuid.UUID,
        prev_state: str,
        new_state: str,
        fill_price: Decimal | None = None,
        fill_qty: int | None = None,
        reason: str | None = None,
        raw_response: dict | None = None,
    ) -> None:
        event = OrderEvent(
            order_id=order_id,
            previous_state=prev_state,
            new_state=new_state,
            fill_price=fill_price,
            fill_quantity=fill_qty,
            raw_broker_response=raw_response,
            reason=reason,
        )
        self._db.add(event)

    # ------------------------------------------------------------------
    # Bracket order construction
    # ------------------------------------------------------------------

    async def construct_bracket_order(
        self, signal: Signal, quantity: int
    ) -> str:
        """Create 3 Order records (ENTRY + SL + TP) with shared bracket_group_id.

        Returns the bracket_group_id.
        """
        bracket_group_id = uuid.uuid4()
        direction = signal.direction

        # Determine sides: LONG entry=BUY SL=SELL TP=SELL; SHORT entry=SELL SL=BUY TP=BUY
        if direction == "LONG":
            entry_side = "BUY"
            exit_side = "SELL"
        else:
            entry_side = "SELL"
            exit_side = "BUY"

        # Entry order type
        entry_type = "MARKET" if signal.entry_type == "MARKET" else "LIMIT"

        # Entry order
        entry_order = Order(
            signal_id=signal.id,
            bracket_group_id=bracket_group_id,
            user_id=signal.user_id,
            instrument_symbol=signal.instrument_symbol,
            side=entry_side,
            order_type=entry_type,
            bracket_role="ENTRY",
            price=signal.entry_price if entry_type == "LIMIT" else signal.entry_price,
            quantity=quantity,
            time_in_force="GTC",
            status="CONSTRUCTED",
        )
        self._db.add(entry_order)

        # Stop loss order
        if signal.stop_loss_price is not None:
            sl_order = Order(
                signal_id=signal.id,
                bracket_group_id=bracket_group_id,
                user_id=signal.user_id,
                instrument_symbol=signal.instrument_symbol,
                side=exit_side,
                order_type="STOP",
                bracket_role="STOP_LOSS",
                price=signal.stop_loss_price,
                quantity=quantity,
                time_in_force="GTC",
                status="CONSTRUCTED",
            )
            self._db.add(sl_order)

        # Take profit order
        if signal.take_profit_price is not None:
            tp_order = Order(
                signal_id=signal.id,
                bracket_group_id=bracket_group_id,
                user_id=signal.user_id,
                instrument_symbol=signal.instrument_symbol,
                side=exit_side,
                order_type="LIMIT",
                bracket_role="TAKE_PROFIT",
                price=signal.take_profit_price,
                quantity=quantity,
                time_in_force="GTC",
                status="CONSTRUCTED",
            )
            self._db.add(tp_order)

        await self._db.flush()

        logger.info(
            "Bracket order constructed",
            bracket_group_id=str(bracket_group_id),
            signal_id=str(signal.id),
            direction=direction,
            quantity=quantity,
        )
        return str(bracket_group_id)

    # ------------------------------------------------------------------
    # Order submission
    # ------------------------------------------------------------------

    async def submit_bracket_order(
        self, user_id: uuid.UUID, bracket_group_id: str, adapter: BrokerAdapter
    ) -> dict:
        """Load orders from DB, convert to adapter types, submit to broker."""
        bg_uuid = uuid.UUID(bracket_group_id)

        # Load all orders in the bracket group
        stmt = (
            select(Order)
            .where(
                Order.bracket_group_id == bg_uuid,
                Order.user_id == user_id,
            )
            .order_by(Order.bracket_role)
        )
        result = await self._db.execute(stmt)
        orders = list(result.scalars().all())

        if not orders:
            raise NotFoundError("BracketGroup", bracket_group_id)

        entry_order = None
        sl_order = None
        tp_order = None

        for o in orders:
            if o.bracket_role == "ENTRY":
                entry_order = o
            elif o.bracket_role == "STOP_LOSS":
                sl_order = o
            elif o.bracket_role == "TAKE_PROFIT":
                tp_order = o

        if entry_order is None:
            raise NotFoundError("Entry order in bracket group", bracket_group_id)

        # Convert to adapter OrderRequest types
        entry_req = self._to_order_request(entry_order, bracket_group_id)
        sl_req = self._to_order_request(sl_order, bracket_group_id) if sl_order else None
        tp_req = self._to_order_request(tp_order, bracket_group_id) if tp_order else None

        # Submit to broker
        if sl_req and tp_req:
            bracket_result = await adapter.place_bracket_order(entry_req, sl_req, tp_req)

            # Update entry order
            entry_order.broker_order_id = bracket_result.entry.broker_order_id
            entry_order.status = bracket_result.entry.status
            entry_order.submitted_at = datetime.now(UTC)
            await self._record_order_event(
                entry_order.id, "CONSTRUCTED", bracket_result.entry.status,
            )
            if bracket_result.entry.fill_price:
                entry_order.fill_price = bracket_result.entry.fill_price
                entry_order.filled_quantity = bracket_result.entry.fill_quantity
                entry_order.commission = bracket_result.entry.commission
                entry_order.filled_at = bracket_result.entry.timestamp
                if bracket_result.entry.status == "FILLED":
                    await self._record_order_event(
                        entry_order.id, "SUBMITTED", "FILLED",
                        fill_price=bracket_result.entry.fill_price,
                        fill_qty=bracket_result.entry.fill_quantity,
                    )

            # Update SL order
            sl_order.broker_order_id = bracket_result.stop_loss.broker_order_id
            sl_order.status = bracket_result.stop_loss.status
            sl_order.submitted_at = datetime.now(UTC)
            await self._record_order_event(
                sl_order.id, "CONSTRUCTED", bracket_result.stop_loss.status,
            )

            # Update TP order
            tp_order.broker_order_id = bracket_result.take_profit.broker_order_id
            tp_order.status = bracket_result.take_profit.status
            tp_order.submitted_at = datetime.now(UTC)
            await self._record_order_event(
                tp_order.id, "CONSTRUCTED", bracket_result.take_profit.status,
            )
        else:
            # Submit entry only
            entry_result = await adapter.place_order(entry_req)
            entry_order.broker_order_id = entry_result.broker_order_id
            entry_order.status = entry_result.status
            entry_order.submitted_at = datetime.now(UTC)
            await self._record_order_event(
                entry_order.id, "CONSTRUCTED", entry_result.status,
            )
            if entry_result.fill_price:
                entry_order.fill_price = entry_result.fill_price
                entry_order.filled_quantity = entry_result.fill_quantity
                entry_order.commission = entry_result.commission
                entry_order.filled_at = entry_result.timestamp
                if entry_result.status == "FILLED":
                    await self._record_order_event(
                        entry_order.id, "SUBMITTED", "FILLED",
                        fill_price=entry_result.fill_price,
                        fill_qty=entry_result.fill_quantity,
                    )

        # If entry filled, create position
        if entry_order.status == "FILLED":
            await self._create_position_from_fill(entry_order)

        await self._db.commit()

        logger.info(
            "Bracket order submitted",
            bracket_group_id=bracket_group_id,
            entry_status=entry_order.status,
        )
        return {
            "bracket_group_id": bracket_group_id,
            "entry_status": entry_order.status,
            "entry_fill_price": float(entry_order.fill_price) if entry_order.fill_price else None,
        }

    # ------------------------------------------------------------------
    # Fill processing
    # ------------------------------------------------------------------

    async def process_fill(
        self, order_id: uuid.UUID, fill_data: dict
    ) -> None:
        """Update order on fill, create/close position as needed."""
        stmt = select(Order).where(Order.id == order_id)
        result = await self._db.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            raise NotFoundError("Order", str(order_id))

        old_status = order.status
        order.status = "FILLED"
        order.fill_price = Decimal(str(fill_data["fill_price"]))
        order.filled_quantity = fill_data.get("fill_quantity", order.quantity)
        order.commission = (
            Decimal(str(fill_data["commission"]))
            if fill_data.get("commission")
            else None
        )
        order.filled_at = datetime.now(UTC)
        await self._record_order_event(
            order.id, old_status, "FILLED",
            fill_price=order.fill_price,
            fill_qty=order.filled_quantity,
        )

        if order.bracket_role == "ENTRY":
            await self._create_position_from_fill(order)
        elif order.bracket_role in ("STOP_LOSS", "TAKE_PROFIT"):
            exit_reason = (
                "STOP_LOSS" if order.bracket_role == "STOP_LOSS" else "TAKE_PROFIT"
            )
            await self._close_position_from_fill(order, exit_reason)
            # OCO: cancel the other pending order
            await self.handle_oco_fill(order.id, order.bracket_group_id)

        await self._db.commit()

    async def handle_oco_fill(
        self, filled_order_id: uuid.UUID, bracket_group_id: uuid.UUID
    ) -> None:
        """Cancel the other pending order in the bracket group (OCO behavior)."""
        stmt = select(Order).where(
            Order.bracket_group_id == bracket_group_id,
            Order.id != filled_order_id,
            Order.bracket_role != "ENTRY",
            Order.status.in_(["CONSTRUCTED", "SUBMITTED"]),
        )
        result = await self._db.execute(stmt)
        pending_orders = list(result.scalars().all())

        for order in pending_orders:
            old_status = order.status
            order.status = "CANCELLED"
            await self._record_order_event(
                order.id, old_status, "CANCELLED", reason="OCO fill",
            )
            logger.info(
                "OCO cancelled order",
                order_id=str(order.id),
                bracket_role=order.bracket_role,
                bracket_group_id=str(bracket_group_id),
            )

    # ------------------------------------------------------------------
    # Position management
    # ------------------------------------------------------------------

    async def close_position(
        self, user_id: uuid.UUID, position_id: uuid.UUID, adapter: BrokerAdapter
    ) -> dict:
        """Close a position: place market exit, cancel pending SL/TP, finalize P&L."""
        stmt = select(Position).where(
            Position.id == position_id,
            Position.user_id == user_id,
            Position.status == "OPEN",
        )
        result = await self._db.execute(stmt)
        position = result.scalar_one_or_none()
        if position is None:
            raise NotFoundError("Position", str(position_id))

        # Place market close order
        close_side = OrderSide.SELL if position.direction == "LONG" else OrderSide.BUY
        close_req = OrderRequest(
            instrument_symbol=position.instrument_symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            quantity=position.quantity,
            price=position.current_price,
            client_order_id=f"close-{position_id}",
        )
        close_result = await adapter.place_order(close_req)

        # Create close order record
        close_order = Order(
            signal_id=position.signal_id,
            bracket_group_id=uuid.uuid4(),  # Standalone close
            user_id=user_id,
            instrument_symbol=position.instrument_symbol,
            side=close_side.value,
            order_type="MARKET",
            bracket_role="ENTRY",  # Close is technically an entry in opposite direction
            price=close_result.fill_price,
            quantity=position.quantity,
            status=close_result.status,
            broker_order_id=close_result.broker_order_id,
            fill_price=close_result.fill_price,
            filled_quantity=close_result.fill_quantity,
            commission=close_result.commission,
            submitted_at=datetime.now(UTC),
            filled_at=close_result.timestamp,
        )
        self._db.add(close_order)
        await self._db.flush()
        await self._record_order_event(
            close_order.id, "CONSTRUCTED", close_result.status,
            fill_price=close_result.fill_price,
            fill_qty=close_result.fill_quantity,
            reason="Position close",
        )

        # Cancel pending SL/TP orders for this position's signal
        if position.entry_order_id:
            entry_stmt = select(Order).where(Order.id == position.entry_order_id)
            entry_result = await self._db.execute(entry_stmt)
            entry_order = entry_result.scalar_one_or_none()
            if entry_order:
                await self._cancel_bracket_pending(entry_order.bracket_group_id, adapter)

        # Calculate final P&L
        exit_price = float(close_result.fill_price) if close_result.fill_price else 0.0
        await self._finalize_position(position, exit_price, "MANUAL")

        await self._db.commit()

        logger.info(
            "Position closed",
            position_id=str(position_id),
            exit_price=exit_price,
            net_pnl=float(position.net_pnl) if position.net_pnl else None,
        )
        return {
            "position": self._position_to_dict(position),
            "closing_order": self._order_to_dict(close_order),
        }

    async def flatten_all(
        self, user_id: uuid.UUID, adapter: BrokerAdapter
    ) -> dict:
        """Close all open positions and cancel all pending orders."""
        # Get all open positions
        pos_stmt = select(Position).where(
            Position.user_id == user_id,
            Position.status == "OPEN",
        )
        pos_result = await self._db.execute(pos_stmt)
        positions = list(pos_result.scalars().all())

        closed_positions = []
        for pos in positions:
            try:
                result = await self.close_position(user_id, pos.id, adapter)
                closed_positions.append(result["position"])
            except Exception:
                logger.error(
                    "Failed to close position during flatten",
                    position_id=str(pos.id),
                    exc_info=True,
                )

        # Cancel any remaining pending orders
        pending_stmt = select(Order).where(
            Order.user_id == user_id,
            Order.status.in_(["CONSTRUCTED", "SUBMITTED"]),
        )
        pending_result = await self._db.execute(pending_stmt)
        pending_orders = list(pending_result.scalars().all())
        cancelled_count = 0
        for order in pending_orders:
            old_status = order.status
            order.status = "CANCELLED"
            await self._record_order_event(
                order.id, old_status, "CANCELLED", reason="Flatten all",
            )
            cancelled_count += 1

        await self._db.commit()

        logger.info(
            "Flatten all complete",
            user_id=str(user_id),
            closed_count=len(closed_positions),
            cancelled_orders=cancelled_count,
        )
        return {
            "closed_count": len(closed_positions),
            "cancelled_orders": cancelled_count,
            "positions": closed_positions,
        }

    async def cancel_order(
        self, user_id: uuid.UUID, order_id: uuid.UUID, adapter: BrokerAdapter
    ) -> dict:
        """Cancel an order (must be CONSTRUCTED or SUBMITTED)."""
        stmt = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            raise NotFoundError("Order", str(order_id))

        if order.status not in ("CONSTRUCTED", "SUBMITTED"):
            raise ConflictError(
                f"Cannot cancel order in '{order.status}' status."
            )

        if order.broker_order_id:
            cancel_result = await adapter.cancel_order(order.broker_order_id)
            if not cancel_result.success:
                raise ConflictError(f"Broker cancel failed: {cancel_result.message}")

        old_status = order.status
        order.status = "CANCELLED"
        await self._record_order_event(
            order.id, old_status, "CANCELLED", reason="User cancel",
        )
        await self._db.commit()

        logger.info("Order cancelled", order_id=str(order_id))
        return self._order_to_dict(order)

    async def modify_order(
        self,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
        mods: dict,
        adapter: BrokerAdapter,
    ) -> dict:
        """Modify a pending order's price or quantity."""
        stmt = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            raise NotFoundError("Order", str(order_id))

        if order.status not in ("CONSTRUCTED", "SUBMITTED"):
            raise ConflictError(
                f"Cannot modify order in '{order.status}' status."
            )

        new_price = mods.get("new_price")
        new_quantity = mods.get("new_quantity")

        if order.broker_order_id:
            mod_result = await adapter.modify_order(
                order.broker_order_id,
                new_price=new_price,
                new_quantity=new_quantity,
            )
            if not mod_result.success:
                raise ConflictError(f"Broker modify failed: {mod_result.message}")

        if new_price is not None:
            order.price = Decimal(str(new_price))
        if new_quantity is not None:
            order.quantity = new_quantity

        await self._db.commit()

        logger.info(
            "Order modified",
            order_id=str(order_id),
            new_price=new_price,
            new_quantity=new_quantity,
        )
        return self._order_to_dict(order)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_positions(
        self,
        user_id: uuid.UUID,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """List positions with pagination."""
        base = select(Position).where(Position.user_id == user_id)
        count_q = select(func.count()).select_from(Position).where(
            Position.user_id == user_id
        )

        if status_filter:
            base = base.where(Position.status == status_filter)
            count_q = count_q.where(Position.status == status_filter)

        total_result = await self._db.execute(count_q)
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        stmt = base.order_by(Position.created_at.desc()).offset(offset).limit(per_page)
        result = await self._db.execute(stmt)
        positions = list(result.scalars().all())

        return {
            "positions": [self._position_to_dict(p) for p in positions],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    async def get_orders(
        self,
        user_id: uuid.UUID,
        status_filter: str | None = None,
        bracket_group_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """List orders with pagination."""
        base = select(Order).where(Order.user_id == user_id)
        count_q = select(func.count()).select_from(Order).where(
            Order.user_id == user_id
        )

        if status_filter:
            base = base.where(Order.status == status_filter)
            count_q = count_q.where(Order.status == status_filter)
        if bracket_group_id:
            bg_uuid = uuid.UUID(bracket_group_id)
            base = base.where(Order.bracket_group_id == bg_uuid)
            count_q = count_q.where(Order.bracket_group_id == bg_uuid)

        total_result = await self._db.execute(count_q)
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        stmt = base.order_by(Order.created_at.desc()).offset(offset).limit(per_page)
        result = await self._db.execute(stmt)
        orders = list(result.scalars().all())

        return {
            "orders": [self._order_to_dict(o) for o in orders],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    async def get_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> dict:
        """Get a single order."""
        stmt = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            raise NotFoundError("Order", str(order_id))
        return self._order_to_dict(order)

    async def get_position(self, user_id: uuid.UUID, position_id: uuid.UUID) -> dict:
        """Get a single position."""
        stmt = select(Position).where(
            Position.id == position_id,
            Position.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        position = result.scalar_one_or_none()
        if position is None:
            raise NotFoundError("Position", str(position_id))
        return self._position_to_dict(position)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _create_position_from_fill(self, entry_order: Order) -> Position:
        """Create an OPEN position from a filled entry order."""
        # Load signal for SL/TP prices
        signal = None
        if entry_order.signal_id:
            sig_stmt = select(Signal).where(Signal.id == entry_order.signal_id)
            sig_result = await self._db.execute(sig_stmt)
            signal = sig_result.scalar_one_or_none()

        position = Position(
            signal_id=entry_order.signal_id,
            entry_order_id=entry_order.id,
            user_id=entry_order.user_id,
            instrument_symbol=entry_order.instrument_symbol,
            direction="LONG" if entry_order.side == "BUY" else "SHORT",
            entry_price=entry_order.fill_price or entry_order.price,
            current_price=entry_order.fill_price or entry_order.price,
            stop_loss_price=signal.stop_loss_price if signal else None,
            take_profit_price=signal.take_profit_price if signal else None,
            quantity=entry_order.filled_quantity or entry_order.quantity,
            unrealized_pnl=Decimal("0"),
            status="OPEN",
            entered_at=entry_order.filled_at or datetime.now(UTC),
        )
        self._db.add(position)
        await self._db.flush()

        logger.info(
            "Position opened",
            position_id=str(position.id),
            instrument=position.instrument_symbol,
            direction=position.direction,
            entry_price=float(position.entry_price),
        )
        return position

    async def _close_position_from_fill(
        self, exit_order: Order, exit_reason: str
    ) -> None:
        """Close the position associated with this bracket group's signal."""
        # Find open position for this signal
        stmt = select(Position).where(
            Position.user_id == exit_order.user_id,
            Position.instrument_symbol == exit_order.instrument_symbol,
            Position.status == "OPEN",
        )
        if exit_order.signal_id:
            stmt = stmt.where(Position.signal_id == exit_order.signal_id)

        result = await self._db.execute(stmt)
        position = result.scalars().first()
        if position is None:
            logger.warning(
                "No open position found for exit fill",
                order_id=str(exit_order.id),
                signal_id=str(exit_order.signal_id),
            )
            return

        exit_price = float(exit_order.fill_price) if exit_order.fill_price else 0.0
        await self._finalize_position(position, exit_price, exit_reason)

    async def _finalize_position(
        self, position: Position, exit_price: float, exit_reason: str
    ) -> None:
        """Calculate final P&L, R-multiple, and close the position."""
        entry_price = float(position.entry_price)
        quantity = position.quantity

        # Look up contract spec for tick calculations
        tick_size = 0.25
        tick_value = 12.50
        spec_stmt = select(ContractSpecification).where(
            ContractSpecification.symbol == position.instrument_symbol
        )
        spec_result = await self._db.execute(spec_stmt)
        spec = spec_result.scalar_one_or_none()
        if spec:
            tick_size = float(spec.tick_size)
            tick_value = float(spec.tick_value)

        if position.direction == "LONG":
            raw_pnl = (exit_price - entry_price) / tick_size * tick_value * quantity
        else:
            raw_pnl = (entry_price - exit_price) / tick_size * tick_value * quantity

        position.realized_pnl = Decimal(str(round(raw_pnl, 2)))
        position.net_pnl = position.realized_pnl  # Simplified; could subtract commissions
        position.unrealized_pnl = Decimal("0")
        position.current_price = Decimal(str(exit_price))
        position.status = "CLOSED"
        position.exit_reason = exit_reason
        position.closed_at = datetime.now(UTC)

        # R-multiple
        if position.stop_loss_price is not None:
            stop = float(position.stop_loss_price)
            risk_per_contract = abs(entry_price - stop) / tick_size * tick_value
            planned_risk = risk_per_contract * quantity
            if planned_risk > 0:
                position.r_multiple = Decimal(
                    str(round(float(position.net_pnl) / planned_risk, 4))
                )

    async def _cancel_bracket_pending(
        self, bracket_group_id: uuid.UUID, adapter: BrokerAdapter
    ) -> None:
        """Cancel all pending orders in a bracket group."""
        stmt = select(Order).where(
            Order.bracket_group_id == bracket_group_id,
            Order.status.in_(["CONSTRUCTED", "SUBMITTED"]),
        )
        result = await self._db.execute(stmt)
        pending = list(result.scalars().all())

        for order in pending:
            if order.broker_order_id:
                try:
                    await adapter.cancel_order(order.broker_order_id)
                except Exception:
                    logger.warning(
                        "Failed to cancel order at broker",
                        order_id=str(order.id),
                        exc_info=True,
                    )
            order.status = "CANCELLED"

    @staticmethod
    def _to_order_request(order: Order, bracket_group_id: str) -> OrderRequest:
        """Convert an Order ORM model to an adapter OrderRequest."""
        return OrderRequest(
            instrument_symbol=order.instrument_symbol,
            side=OrderSide(order.side),
            order_type=OrderType(order.order_type),
            quantity=order.quantity,
            price=order.price,
            time_in_force=order.time_in_force,
            bracket_role=BracketRole(order.bracket_role),
            bracket_group_id=bracket_group_id,
            client_order_id=str(order.id),
        )

    @staticmethod
    def _order_to_dict(order: Order) -> dict:
        """Convert Order ORM to response dict."""
        return {
            "id": str(order.id),
            "signal_id": str(order.signal_id) if order.signal_id else None,
            "bracket_group_id": str(order.bracket_group_id),
            "instrument_symbol": order.instrument_symbol,
            "side": order.side,
            "order_type": order.order_type,
            "bracket_role": order.bracket_role,
            "price": float(order.price) if order.price else None,
            "quantity": order.quantity,
            "time_in_force": order.time_in_force,
            "status": order.status,
            "broker_order_id": order.broker_order_id,
            "fill_price": float(order.fill_price) if order.fill_price else None,
            "filled_quantity": order.filled_quantity,
            "commission": float(order.commission) if order.commission else None,
            "slippage_ticks": order.slippage_ticks,
            "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
            "created_at": order.created_at.isoformat(),
        }

    @staticmethod
    def _position_to_dict(position: Position) -> dict:
        """Convert Position ORM to response dict."""
        return {
            "id": str(position.id),
            "signal_id": str(position.signal_id) if position.signal_id else None,
            "instrument_symbol": position.instrument_symbol,
            "direction": position.direction,
            "entry_price": float(position.entry_price),
            "current_price": float(position.current_price) if position.current_price else None,
            "stop_loss_price": float(position.stop_loss_price) if position.stop_loss_price else None,
            "take_profit_price": float(position.take_profit_price) if position.take_profit_price else None,
            "quantity": position.quantity,
            "unrealized_pnl": float(position.unrealized_pnl),
            "realized_pnl": float(position.realized_pnl) if position.realized_pnl else None,
            "net_pnl": float(position.net_pnl) if position.net_pnl else None,
            "r_multiple": float(position.r_multiple) if position.r_multiple else None,
            "mae": float(position.mae) if position.mae else None,
            "mfe": float(position.mfe) if position.mfe else None,
            "status": position.status,
            "exit_reason": position.exit_reason,
            "entered_at": position.entered_at.isoformat(),
            "closed_at": position.closed_at.isoformat() if position.closed_at else None,
            "created_at": position.created_at.isoformat(),
        }
