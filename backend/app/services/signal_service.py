"""Signal intake, validation, enrichment, and deduplication."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.db.models.contract_specification import ContractSpecification
from app.db.models.risk_check_audit import RiskCheckAudit
from app.db.models.signal import Signal
from app.db.models.trendline import Trendline
from app.db.models.webhook_url import WebhookUrl

logger = get_logger("trendedge.signal_service")

# Signal dedup window in seconds
_DEDUP_TTL = 300


class SignalService:
    """Handles signal creation, validation, enrichment, and querying."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None) -> None:
        self._db = db
        self._redis = redis

    # ------------------------------------------------------------------
    # Signal creation
    # ------------------------------------------------------------------

    async def create_manual_signal(
        self, user_id: uuid.UUID, payload: dict
    ) -> Signal:
        """Create a manual trading signal.

        Validates the instrument, checks for dedup, persists the Signal,
        and dispatches the process_signal Celery task.
        """
        contract_spec = await self.validate_instrument(payload["instrument_symbol"])

        self.validate_prices(
            direction=payload["direction"],
            entry_price=payload["entry_price"],
            stop_loss_price=payload.get("stop_loss_price"),
            take_profit_price=payload.get("take_profit_price"),
            tick_size=float(contract_spec.tick_size),
        )

        await self.deduplicate_signal(
            user_id,
            payload["instrument_symbol"],
            payload["direction"],
        )

        # Look up trendline grade if linked
        trendline_grade = None
        if payload.get("trendline_id"):
            tl_stmt = select(Trendline).where(
                Trendline.id == uuid.UUID(payload["trendline_id"]),
                Trendline.user_id == user_id,
            )
            tl_result = await self._db.execute(tl_stmt)
            tl = tl_result.scalar_one_or_none()
            if tl:
                trendline_grade = tl.grade

        signal = Signal(
            user_id=user_id,
            source="MANUAL",
            status="RECEIVED",
            instrument_symbol=payload["instrument_symbol"],
            direction=payload["direction"],
            entry_type=payload.get("entry_type", "MARKET"),
            entry_price=Decimal(str(payload["entry_price"])),
            stop_loss_price=(
                Decimal(str(payload["stop_loss_price"]))
                if payload.get("stop_loss_price")
                else None
            ),
            take_profit_price=(
                Decimal(str(payload["take_profit_price"]))
                if payload.get("take_profit_price")
                else None
            ),
            quantity=payload.get("quantity"),
            trendline_id=(
                uuid.UUID(payload["trendline_id"])
                if payload.get("trendline_id")
                else None
            ),
            trendline_grade=trendline_grade,
            source_metadata={"notes": payload.get("notes")},
        )
        self._db.add(signal)
        await self._db.flush()

        # Enrich the signal
        enrichment = self.enrich_signal(signal, contract_spec)
        signal.enrichment_data = enrichment
        signal.status = "ENRICHED"
        await self._db.commit()
        await self._db.refresh(signal)

        # Dispatch processing task
        try:
            from app.tasks.execution_tasks import process_signal

            process_signal.delay(str(signal.id))
        except Exception:
            logger.warning(
                "Failed to dispatch process_signal task",
                signal_id=str(signal.id),
                exc_info=True,
            )

        logger.info(
            "Manual signal created",
            signal_id=str(signal.id),
            user_id=str(user_id),
            instrument=payload["instrument_symbol"],
            direction=payload["direction"],
        )
        return signal

    async def process_webhook_signal(
        self, webhook_id: str, payload: dict
    ) -> Signal:
        """Process an inbound TradingView webhook.

        Looks up the webhook URL, normalizes the payload, creates the Signal,
        and dispatches processing.
        """
        # Look up webhook
        stmt = select(WebhookUrl).where(
            WebhookUrl.webhook_id == webhook_id,
            WebhookUrl.is_active == True,  # noqa: E712
        )
        result = await self._db.execute(stmt)
        webhook = result.scalar_one_or_none()
        if webhook is None:
            raise NotFoundError("Webhook", webhook_id)

        # Update webhook stats
        webhook.last_received_at = datetime.now(UTC)
        webhook.request_count = webhook.request_count + 1

        # Normalize TV payload to canonical format
        normalized = self.normalize_signal("WEBHOOK", payload)

        contract_spec = await self.validate_instrument(normalized["instrument_symbol"])

        signal = Signal(
            user_id=webhook.user_id,
            source="WEBHOOK",
            status="RECEIVED",
            instrument_symbol=normalized["instrument_symbol"],
            direction=normalized["direction"],
            entry_type="MARKET",
            entry_price=Decimal(str(normalized["entry_price"])),
            stop_loss_price=(
                Decimal(str(normalized["stop_loss_price"]))
                if normalized.get("stop_loss_price")
                else None
            ),
            take_profit_price=(
                Decimal(str(normalized["take_profit_price"]))
                if normalized.get("take_profit_price")
                else None
            ),
            quantity=normalized.get("quantity"),
            webhook_url_id=webhook.id,
            source_metadata={
                "raw_payload": payload,
                "timeframe": payload.get("timeframe"),
                "exchange": payload.get("exchange"),
                "message": payload.get("message"),
            },
        )
        self._db.add(signal)
        await self._db.flush()

        enrichment = self.enrich_signal(signal, contract_spec)
        signal.enrichment_data = enrichment
        signal.status = "ENRICHED"
        await self._db.commit()
        await self._db.refresh(signal)

        # Dispatch processing
        try:
            from app.tasks.execution_tasks import process_signal

            process_signal.delay(str(signal.id))
        except Exception:
            logger.warning(
                "Failed to dispatch process_signal task for webhook",
                signal_id=str(signal.id),
                exc_info=True,
            )

        logger.info(
            "Webhook signal created",
            signal_id=str(signal.id),
            webhook_id=webhook_id,
            instrument=normalized["instrument_symbol"],
        )
        return signal

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_signal(source: str, raw_payload: dict) -> dict:
        """Map TradingView fields to canonical signal format."""
        if source == "WEBHOOK":
            return {
                "instrument_symbol": raw_payload["ticker"],
                "direction": "LONG" if raw_payload["action"] == "buy" else "SHORT",
                "entry_price": raw_payload["price"],
                "stop_loss_price": raw_payload.get("stop"),
                "take_profit_price": raw_payload.get("target"),
                "quantity": raw_payload.get("quantity"),
            }
        return raw_payload

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    async def validate_instrument(self, symbol: str) -> ContractSpecification:
        """Look up the contract specification for an instrument symbol."""
        stmt = select(ContractSpecification).where(
            ContractSpecification.symbol == symbol
        )
        result = await self._db.execute(stmt)
        spec = result.scalar_one_or_none()
        if spec is None:
            raise NotFoundError("Instrument", symbol)
        return spec

    @staticmethod
    def validate_prices(
        direction: str,
        entry_price: float,
        stop_loss_price: float | None,
        take_profit_price: float | None,
        tick_size: float,
    ) -> None:
        """Validate price relationships and minimum tick distance."""
        if stop_loss_price is not None:
            if direction == "LONG" and stop_loss_price >= entry_price:
                raise ValueError("Stop loss must be below entry for LONG")
            if direction == "SHORT" and stop_loss_price <= entry_price:
                raise ValueError("Stop loss must be above entry for SHORT")
            if abs(entry_price - stop_loss_price) < tick_size:
                raise ValueError("Stop must be at least 1 tick from entry")

        if take_profit_price is not None:
            if direction == "LONG" and take_profit_price <= entry_price:
                raise ValueError("Take profit must be above entry for LONG")
            if direction == "SHORT" and take_profit_price >= entry_price:
                raise ValueError("Take profit must be below entry for SHORT")
            if abs(take_profit_price - entry_price) < tick_size:
                raise ValueError("Target must be at least 1 tick from entry")

    # ------------------------------------------------------------------
    # Enrichment
    # ------------------------------------------------------------------

    @staticmethod
    def enrich_signal(signal: Signal, contract_spec: ContractSpecification) -> dict:
        """Compute risk/reward metrics and store in enrichment_data."""
        entry = float(signal.entry_price)
        tick_size = float(contract_spec.tick_size)
        tick_value = float(contract_spec.tick_value)
        enrichment: dict = {
            "tick_size": tick_size,
            "tick_value": tick_value,
            "point_value": float(contract_spec.point_value),
            "is_micro": contract_spec.is_micro,
        }

        if signal.stop_loss_price is not None:
            stop = float(signal.stop_loss_price)
            risk_distance = abs(entry - stop)
            risk_ticks = risk_distance / tick_size if tick_size > 0 else 0
            risk_per_contract = risk_ticks * tick_value
            enrichment["risk_distance"] = round(risk_distance, 4)
            enrichment["risk_ticks"] = round(risk_ticks, 2)
            enrichment["risk_per_contract"] = round(risk_per_contract, 2)

            if signal.take_profit_price is not None:
                target = float(signal.take_profit_price)
                reward_distance = abs(target - entry)
                reward_ticks = reward_distance / tick_size if tick_size > 0 else 0
                reward_per_contract = reward_ticks * tick_value
                rr_ratio = (
                    reward_per_contract / risk_per_contract
                    if risk_per_contract > 0
                    else 0
                )
                enrichment["reward_distance"] = round(reward_distance, 4)
                enrichment["reward_ticks"] = round(reward_ticks, 2)
                enrichment["reward_per_contract"] = round(reward_per_contract, 2)
                enrichment["risk_reward_ratio"] = round(rr_ratio, 2)

        return enrichment

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    async def deduplicate_signal(
        self, user_id: uuid.UUID, instrument: str, direction: str
    ) -> None:
        """Check Redis for a recent duplicate signal. Raises ConflictError if found."""
        if self._redis is None:
            return
        key = f"dedup:{user_id}:{instrument}:{direction}"
        existing = await self._redis.get(key)
        if existing:
            raise ConflictError(
                f"Duplicate signal for {instrument} {direction} within "
                f"{_DEDUP_TTL}s window."
            )
        await self._redis.set(key, "1", ex=_DEDUP_TTL)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_signal(
        self, user_id: uuid.UUID, signal_id: uuid.UUID
    ) -> dict:
        """Get a signal with its risk check audit records."""
        stmt = select(Signal).where(
            Signal.id == signal_id,
            Signal.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        signal = result.scalar_one_or_none()
        if signal is None:
            raise NotFoundError("Signal", str(signal_id))

        # Load risk checks
        checks_stmt = select(RiskCheckAudit).where(
            RiskCheckAudit.signal_id == signal_id
        )
        checks_result = await self._db.execute(checks_stmt)
        checks = list(checks_result.scalars().all())

        return self._signal_to_dict(signal, checks)

    async def list_signals(
        self,
        user_id: uuid.UUID,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """List signals with pagination and optional status filter."""
        base_query = select(Signal).where(Signal.user_id == user_id)
        count_query = select(func.count()).select_from(Signal).where(
            Signal.user_id == user_id
        )

        if status_filter:
            base_query = base_query.where(Signal.status == status_filter)
            count_query = count_query.where(Signal.status == status_filter)

        # Total count
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginated results
        offset = (page - 1) * per_page
        stmt = (
            base_query.order_by(Signal.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self._db.execute(stmt)
        signals = list(result.scalars().all())

        return {
            "signals": [self._signal_to_dict(s) for s in signals],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _signal_to_dict(
        signal: Signal, checks: list[RiskCheckAudit] | None = None
    ) -> dict:
        """Convert Signal ORM to response dict."""
        d = {
            "id": str(signal.id),
            "source": signal.source,
            "status": signal.status,
            "instrument_symbol": signal.instrument_symbol,
            "direction": signal.direction,
            "entry_type": signal.entry_type,
            "entry_price": float(signal.entry_price),
            "stop_loss_price": (
                float(signal.stop_loss_price) if signal.stop_loss_price else None
            ),
            "take_profit_price": (
                float(signal.take_profit_price) if signal.take_profit_price else None
            ),
            "quantity": signal.quantity,
            "trendline_id": str(signal.trendline_id) if signal.trendline_id else None,
            "trendline_grade": signal.trendline_grade,
            "enrichment_data": signal.enrichment_data,
            "rejection_reason": signal.rejection_reason,
            "created_at": signal.created_at.isoformat(),
            "updated_at": signal.updated_at.isoformat(),
        }
        if checks is not None:
            d["risk_checks"] = [
                {
                    "check_name": c.check_name,
                    "result": c.result,
                    "actual_value": float(c.actual_value) if c.actual_value else None,
                    "threshold_value": (
                        float(c.threshold_value) if c.threshold_value else None
                    ),
                    "details": c.details,
                }
                for c in checks
            ]
        return d
