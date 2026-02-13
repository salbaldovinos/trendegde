"""Celery tasks for trade execution pipeline."""

from __future__ import annotations

import asyncio

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger("trendedge.execution_tasks")


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.execution_tasks.process_signal",
    queue="high",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_signal(self, signal_id: str):
    """Process a signal: run risk checks, calculate quantity, construct bracket, submit.

    Triggered on-demand when a signal is created (manual or webhook).
    """

    async def _run():
        import uuid

        from redis.asyncio import Redis

        from app.core.config import settings
        from app.db.session import AsyncSessionLocal
        from app.services.execution_service import ExecutionService
        from app.services.risk_service import RiskService
        from app.services.signal_service import SignalService

        async with AsyncSessionLocal() as db:
            redis = Redis.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
            try:
                from sqlalchemy import select

                from app.adapters.registry import get_adapter
                from app.db.models.signal import Signal

                # Load signal
                stmt = select(Signal).where(Signal.id == uuid.UUID(signal_id))
                result = await db.execute(stmt)
                signal = result.scalar_one_or_none()
                if signal is None:
                    logger.error("Signal not found", signal_id=signal_id)
                    return

                # Check circuit breaker
                risk_svc = RiskService(db, redis)
                user_id = signal.user_id
                cb_state = await risk_svc.get_circuit_breaker_state(user_id)
                if cb_state["state"] == "TRIPPED":
                    signal.status = "REJECTED"
                    signal.rejection_reason = "Circuit breaker is tripped"
                    await db.commit()
                    logger.warning(
                        "Signal rejected: circuit breaker tripped",
                        signal_id=signal_id,
                        user_id=str(user_id),
                    )
                    return

                # Get risk settings
                risk_settings = await risk_svc.get_risk_settings(user_id)

                # Run risk checks
                signal.status = "VALIDATED"
                check_results = await risk_svc.run_all_checks(signal, risk_settings)

                # Check overall result
                failed = any(c["result"] == "FAIL" for c in check_results)
                if failed:
                    signal.status = "REJECTED"
                    failed_checks = [
                        c["check_name"] for c in check_results if c["result"] == "FAIL"
                    ]
                    signal.rejection_reason = f"Risk check failed: {', '.join(failed_checks)}"
                    await db.commit()
                    logger.info(
                        "Signal rejected by risk checks",
                        signal_id=signal_id,
                        failed_checks=failed_checks,
                    )
                    return

                signal.status = "RISK_PASSED"

                # Calculate quantity
                sig_svc = SignalService(db, redis)
                contract_spec = await sig_svc.validate_instrument(
                    signal.instrument_symbol
                )
                quantity = await risk_svc.calculate_quantity(
                    signal, risk_settings, contract_spec
                )

                # Override with user-specified quantity if set
                if signal.quantity:
                    quantity = signal.quantity

                # Construct bracket order
                exec_svc = ExecutionService(db, redis)
                bracket_group_id = await exec_svc.construct_bracket_order(
                    signal, quantity
                )

                # Submit to broker
                signal.status = "EXECUTING"
                await db.flush()

                adapter = await get_adapter(
                    user_id,
                    db,
                    redis,
                    is_paper=risk_settings["is_paper_mode"],
                    slippage_ticks=risk_settings["paper_slippage_ticks"],
                )
                result = await exec_svc.submit_bracket_order(
                    user_id, bracket_group_id, adapter
                )

                if result["entry_status"] == "FILLED":
                    signal.status = "FILLED"
                else:
                    signal.status = "EXECUTING"

                await db.commit()

                logger.info(
                    "Signal processed successfully",
                    signal_id=signal_id,
                    status=signal.status,
                    bracket_group_id=bracket_group_id,
                    quantity=quantity,
                )

            finally:
                await redis.aclose()

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error("process_signal task failed", signal_id=signal_id, exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.tasks.execution_tasks.monitor_paper_positions",
    queue="detection",
    bind=True,
    max_retries=1,
    default_retry_delay=5,
)
def monitor_paper_positions(self):
    """Monitor open paper positions: check SL/TP triggers, update P&L, track MAE/MFE.

    Beat schedule: every 5 seconds.
    """

    async def _run():
        from decimal import Decimal

        from redis.asyncio import Redis
        from sqlalchemy import select

        from app.core.config import settings
        from app.db.models.contract_specification import ContractSpecification
        from app.db.models.position import Position
        from app.db.session import AsyncSessionLocal
        from app.services.risk_service import RiskService

        async with AsyncSessionLocal() as db:
            redis = Redis.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
            try:
                # Get all open positions (paper mode only tracked here)
                stmt = select(Position).where(Position.status == "OPEN")
                result = await db.execute(stmt)
                positions = list(result.scalars().all())

                if not positions:
                    return

                for position in positions:
                    # Get current price from Redis
                    price_key = f"market:price:{position.instrument_symbol}"
                    raw_price = await redis.get(price_key)
                    if raw_price is None:
                        continue

                    current_price = Decimal(raw_price)
                    position.current_price = current_price

                    # Get contract spec for tick calculations
                    spec_stmt = select(ContractSpecification).where(
                        ContractSpecification.symbol == position.instrument_symbol
                    )
                    spec_result = await db.execute(spec_stmt)
                    spec = spec_result.scalar_one_or_none()
                    tick_size = float(spec.tick_size) if spec else 0.25
                    tick_value = float(spec.tick_value) if spec else 12.50

                    entry = float(position.entry_price)
                    price = float(current_price)
                    qty = position.quantity

                    # Calculate unrealized P&L
                    if position.direction == "LONG":
                        pnl = (price - entry) / tick_size * tick_value * qty
                    else:
                        pnl = (entry - price) / tick_size * tick_value * qty

                    position.unrealized_pnl = Decimal(str(round(pnl, 2)))

                    # Track MAE/MFE
                    if position.direction == "LONG":
                        adverse = entry - price  # negative = good for long
                        favorable = price - entry
                    else:
                        adverse = price - entry  # positive = bad for short
                        favorable = entry - price

                    adverse_price = Decimal(str(round(adverse, 4)))
                    favorable_price = Decimal(str(round(favorable, 4)))

                    if position.mae is None or adverse_price > position.mae:
                        position.mae = adverse_price
                    if position.mfe is None or favorable_price > position.mfe:
                        position.mfe = favorable_price

                    # Track MAE/MFE in R-multiples
                    if position.stop_loss_price is not None:
                        stop = float(position.stop_loss_price)
                        risk_per_contract = abs(entry - stop) / tick_size * tick_value
                        planned_risk = risk_per_contract * qty
                        if planned_risk > 0:
                            mae_pnl = -abs(float(adverse_price)) / tick_size * tick_value * qty
                            mfe_pnl = abs(float(favorable_price)) / tick_size * tick_value * qty
                            position.mae_r = Decimal(
                                str(round(mae_pnl / planned_risk, 4))
                            )
                            position.mfe_r = Decimal(
                                str(round(mfe_pnl / planned_risk, 4))
                            )

                    # Check SL trigger
                    if position.stop_loss_price is not None:
                        sl = float(position.stop_loss_price)
                        triggered = False
                        if position.direction == "LONG" and price <= sl:
                            triggered = True
                        elif position.direction == "SHORT" and price >= sl:
                            triggered = True

                        if triggered:
                            _close_paper_position(
                                position, sl, "STOP_LOSS", tick_size, tick_value
                            )
                            net_pnl = float(position.net_pnl) if position.net_pnl else 0.0
                            risk_svc = RiskService(db, redis)
                            if net_pnl < 0:
                                tripped = await risk_svc.record_loss(position.user_id)
                                if tripped:
                                    logger.warning(
                                        "Circuit breaker tripped after SL",
                                        user_id=str(position.user_id),
                                        position_id=str(position.id),
                                    )
                            else:
                                await risk_svc.record_win(position.user_id)
                            logger.info(
                                "Paper SL triggered",
                                position_id=str(position.id),
                                price=price,
                                stop=sl,
                            )
                            continue

                    # Check TP trigger
                    if position.take_profit_price is not None:
                        tp = float(position.take_profit_price)
                        triggered = False
                        if position.direction == "LONG" and price >= tp:
                            triggered = True
                        elif position.direction == "SHORT" and price <= tp:
                            triggered = True

                        if triggered:
                            _close_paper_position(
                                position, tp, "TAKE_PROFIT", tick_size, tick_value
                            )
                            net_pnl = float(position.net_pnl) if position.net_pnl else 0.0
                            risk_svc = RiskService(db, redis)
                            if net_pnl < 0:
                                tripped = await risk_svc.record_loss(position.user_id)
                                if tripped:
                                    logger.warning(
                                        "Circuit breaker tripped after TP",
                                        user_id=str(position.user_id),
                                        position_id=str(position.id),
                                    )
                            else:
                                await risk_svc.record_win(position.user_id)
                            logger.info(
                                "Paper TP triggered",
                                position_id=str(position.id),
                                price=price,
                                target=tp,
                            )
                            continue

                await db.commit()

            finally:
                await redis.aclose()

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error("monitor_paper_positions task failed", exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.tasks.execution_tasks.reconcile_fills",
    queue="default",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def reconcile_fills(self):
    """Reconcile DB order statuses with broker statuses.

    Beat schedule: every 5 minutes.
    """

    async def _run():
        from redis.asyncio import Redis
        from sqlalchemy import select

        from app.adapters.registry import get_adapter
        from app.core.config import settings
        from app.db.models.order import Order
        from app.db.models.user_risk_settings import UserRiskSettings
        from app.db.session import AsyncSessionLocal
        from app.services.execution_service import ExecutionService

        async with AsyncSessionLocal() as db:
            redis = Redis.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
            try:
                # Get all SUBMITTED orders
                stmt = select(Order).where(
                    Order.status == "SUBMITTED",
                    Order.broker_order_id.isnot(None),
                )
                result = await db.execute(stmt)
                orders = list(result.scalars().all())

                if not orders:
                    return

                # Group by user
                by_user: dict = {}
                for order in orders:
                    uid = order.user_id
                    by_user.setdefault(uid, []).append(order)

                reconciled = 0
                for user_id, user_orders in by_user.items():
                    try:
                        # Get user settings for adapter
                        settings_stmt = select(UserRiskSettings).where(
                            UserRiskSettings.user_id == user_id
                        )
                        settings_result = await db.execute(settings_stmt)
                        risk_settings = settings_result.scalar_one_or_none()
                        is_paper = risk_settings.is_paper_mode if risk_settings else True
                        slippage = (
                            risk_settings.paper_slippage_ticks if risk_settings else 1
                        )

                        adapter = await get_adapter(
                            user_id, db, redis,
                            is_paper=is_paper,
                            slippage_ticks=slippage,
                        )

                        for order in user_orders:
                            try:
                                broker_status = await adapter.get_order_status(
                                    order.broker_order_id
                                )
                                if broker_status.status != order.status:
                                    old_status = order.status
                                    order.status = broker_status.status
                                    if broker_status.fill_price:
                                        order.fill_price = broker_status.fill_price
                                        order.filled_quantity = (
                                            broker_status.filled_quantity
                                        )

                                    # If newly filled, process the fill
                                    if (
                                        broker_status.status == "FILLED"
                                        and old_status != "FILLED"
                                    ):
                                        exec_svc = ExecutionService(db, redis)
                                        await exec_svc.process_fill(
                                            order.id,
                                            {
                                                "fill_price": float(
                                                    broker_status.fill_price or 0
                                                ),
                                                "fill_quantity": (
                                                    broker_status.filled_quantity
                                                ),
                                            },
                                        )

                                    reconciled += 1
                                    logger.info(
                                        "Order status reconciled",
                                        order_id=str(order.id),
                                        old_status=old_status,
                                        new_status=broker_status.status,
                                    )
                            except Exception:
                                logger.warning(
                                    "Failed to reconcile order",
                                    order_id=str(order.id),
                                    exc_info=True,
                                )

                    except Exception:
                        logger.warning(
                            "Failed to get adapter for user during reconciliation",
                            user_id=str(user_id),
                            exc_info=True,
                        )

                if reconciled:
                    await db.commit()

                logger.info(
                    "Fill reconciliation complete",
                    orders_checked=len(orders),
                    reconciled=reconciled,
                )

            finally:
                await redis.aclose()

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error("reconcile_fills task failed", exc_info=True)
        raise self.retry(exc=exc) from exc


def _close_paper_position(position, exit_price, exit_reason, tick_size, tick_value):
    """Close a paper position with final P&L calculation (sync helper)."""
    from datetime import UTC, datetime
    from decimal import Decimal

    entry = float(position.entry_price)
    qty = position.quantity

    if position.direction == "LONG":
        raw_pnl = (exit_price - entry) / tick_size * tick_value * qty
    else:
        raw_pnl = (entry - exit_price) / tick_size * tick_value * qty

    position.realized_pnl = Decimal(str(round(raw_pnl, 2)))
    position.net_pnl = position.realized_pnl
    position.unrealized_pnl = Decimal("0")
    position.current_price = Decimal(str(exit_price))
    position.status = "CLOSED"
    position.exit_reason = exit_reason
    position.closed_at = datetime.now(UTC)

    # R-multiple
    if position.stop_loss_price is not None:
        stop = float(position.stop_loss_price)
        risk_per_contract = abs(entry - stop) / tick_size * tick_value
        planned_risk = risk_per_contract * qty
        if planned_risk > 0:
            position.r_multiple = Decimal(
                str(round(float(position.net_pnl) / planned_risk, 4))
            )
