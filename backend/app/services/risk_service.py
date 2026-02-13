"""Risk management: 8 pre-trade checks, settings CRUD, circuit breaker."""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.db.models.contract_specification import ContractSpecification
from app.db.models.instrument_correlation import InstrumentCorrelation
from app.db.models.position import Position
from app.db.models.risk_check_audit import RiskCheckAudit
from app.db.models.risk_settings_changelog import RiskSettingsChangelog
from app.db.models.signal import Signal
from app.db.models.user_risk_settings import UserRiskSettings

logger = get_logger("trendedge.risk_service")

# Risk settings defaults (must match UserRiskSettings server_defaults)
_DEFAULTS = {
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
    "auto_flatten_loss_limit": None,
    "is_paper_mode": True,
}

# RTH hours in US/Eastern: 08:30 - 15:15
_RTH_START = time(8, 30)
_RTH_END = time(15, 15)
# ETH hours: 18:00 - 17:00 next day (nearly 24H except 17:00-18:00)
_ETH_START = time(18, 0)
_ETH_END = time(17, 0)


class RiskService:
    """Pre-trade risk checks, settings management, and circuit breaker."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None) -> None:
        self._db = db
        self._redis = redis

    # ------------------------------------------------------------------
    # Run all checks
    # ------------------------------------------------------------------

    async def run_all_checks(
        self, signal: Signal, settings: dict
    ) -> list[dict]:
        """Run all 8 risk checks, persist audit records.

        Returns list of check results. Fail-fast on first FAIL.
        """
        contract_spec = await self._get_contract_spec(signal.instrument_symbol)

        checks = [
            ("max_position_size", self.check_max_position_size),
            ("daily_loss_limit", self.check_daily_loss_limit),
            ("max_concurrent_positions", self.check_max_concurrent_positions),
            ("min_risk_reward", self.check_min_risk_reward),
            ("correlation", self.check_correlation),
            ("max_single_trade_risk", self.check_max_single_trade_risk),
            ("trading_hours", self.check_trading_hours),
            ("signal_staleness", self.check_signal_staleness),
        ]

        results: list[dict] = []
        overall = "PASS"

        for check_name, check_fn in checks:
            result = await check_fn(signal, settings, contract_spec)
            result["check_name"] = check_name

            # Persist audit record
            audit = RiskCheckAudit(
                signal_id=signal.id,
                check_name=check_name,
                result=result["result"],
                actual_value=(
                    Decimal(str(result["actual_value"]))
                    if result.get("actual_value") is not None
                    else None
                ),
                threshold_value=(
                    Decimal(str(result["threshold_value"]))
                    if result.get("threshold_value") is not None
                    else None
                ),
                details=result.get("details", {}),
            )
            self._db.add(audit)
            results.append(result)

            if result["result"] == "FAIL":
                overall = "FAIL"
                break  # Fail-fast

        await self._db.flush()

        logger.info(
            "Risk checks complete",
            signal_id=str(signal.id),
            overall=overall,
            checks_run=len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    async def check_max_position_size(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Check if adding this position exceeds max position size for the instrument."""
        max_size = (
            settings["max_position_size_micro"]
            if contract_spec.is_micro
            else settings["max_position_size_full"]
        )

        # Count open positions for this instrument
        stmt = select(func.count()).select_from(Position).where(
            Position.user_id == signal.user_id,
            Position.instrument_symbol == signal.instrument_symbol,
            Position.status == "OPEN",
        )
        result = await self._db.execute(stmt)
        current_count = result.scalar() or 0

        quantity = signal.quantity or 1
        new_total = current_count + quantity

        if new_total > max_size:
            return {
                "result": "FAIL",
                "actual_value": new_total,
                "threshold_value": max_size,
                "details": {
                    "current_positions": current_count,
                    "requested_quantity": quantity,
                    "is_micro": contract_spec.is_micro,
                },
            }
        return {
            "result": "PASS",
            "actual_value": new_total,
            "threshold_value": max_size,
        }

    async def check_daily_loss_limit(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Sum today's realized losses + unrealized losses + worst-case new loss."""
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # Today's realized losses from closed positions
        realized_stmt = select(func.coalesce(func.sum(Position.realized_pnl), 0)).where(
            Position.user_id == signal.user_id,
            Position.status == "CLOSED",
            Position.closed_at >= today_start,
            Position.realized_pnl < 0,
        )
        realized_result = await self._db.execute(realized_stmt)
        realized_losses = abs(float(realized_result.scalar() or 0))

        # Unrealized losses from open positions
        unrealized_stmt = select(
            func.coalesce(func.sum(Position.unrealized_pnl), 0)
        ).where(
            Position.user_id == signal.user_id,
            Position.status == "OPEN",
            Position.unrealized_pnl < 0,
        )
        unrealized_result = await self._db.execute(unrealized_stmt)
        unrealized_losses = abs(float(unrealized_result.scalar() or 0))

        # Worst-case loss for the new signal (all stops hit)
        worst_case = 0.0
        if signal.stop_loss_price is not None:
            enrichment = signal.enrichment_data or {}
            risk_per_contract = enrichment.get("risk_per_contract", 0)
            quantity = signal.quantity or 1
            worst_case = risk_per_contract * quantity

        total_exposure = realized_losses + unrealized_losses + worst_case
        limit = settings["daily_loss_limit"]

        if total_exposure > limit:
            return {
                "result": "FAIL",
                "actual_value": round(total_exposure, 2),
                "threshold_value": limit,
                "details": {
                    "realized_losses": round(realized_losses, 2),
                    "unrealized_losses": round(unrealized_losses, 2),
                    "worst_case_new": round(worst_case, 2),
                },
            }
        return {
            "result": "PASS",
            "actual_value": round(total_exposure, 2),
            "threshold_value": limit,
        }

    async def check_max_concurrent_positions(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Count all open positions across all instruments."""
        stmt = select(func.count()).select_from(Position).where(
            Position.user_id == signal.user_id,
            Position.status == "OPEN",
        )
        result = await self._db.execute(stmt)
        current_count = result.scalar() or 0
        max_concurrent = settings["max_concurrent_positions"]

        if current_count >= max_concurrent:
            return {
                "result": "FAIL",
                "actual_value": current_count,
                "threshold_value": max_concurrent,
            }
        return {
            "result": "PASS",
            "actual_value": current_count,
            "threshold_value": max_concurrent,
        }

    async def check_min_risk_reward(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Compare signal's risk/reward ratio to minimum threshold."""
        min_rr = settings["min_risk_reward"]
        if min_rr == 0:
            return {"result": "SKIP", "actual_value": None, "threshold_value": 0}

        enrichment = signal.enrichment_data or {}
        rr_ratio = enrichment.get("risk_reward_ratio")
        if rr_ratio is None:
            return {
                "result": "WARN",
                "actual_value": None,
                "threshold_value": min_rr,
                "details": {"reason": "No risk/reward ratio available (missing SL or TP)"},
            }

        if rr_ratio < min_rr:
            return {
                "result": "FAIL",
                "actual_value": rr_ratio,
                "threshold_value": min_rr,
            }
        return {
            "result": "PASS",
            "actual_value": rr_ratio,
            "threshold_value": min_rr,
        }

    async def _normalize_symbol(self, symbol: str) -> str:
        """Resolve a micro symbol to its full-size symbol for correlation lookups."""
        stmt = select(ContractSpecification).where(
            ContractSpecification.symbol == symbol
        )
        result = await self._db.execute(stmt)
        spec = result.scalar_one_or_none()
        if spec and spec.full_size_symbol:
            return spec.full_size_symbol
        return symbol

    async def check_correlation(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Check for correlated open positions."""
        corr_limit = settings["correlation_limit"]
        symbol = await self._normalize_symbol(signal.instrument_symbol)

        # Get open position symbols for this user
        open_stmt = (
            select(Position.instrument_symbol)
            .where(
                Position.user_id == signal.user_id,
                Position.status == "OPEN",
            )
            .distinct()
        )
        result = await self._db.execute(open_stmt)
        open_symbols = [row[0] for row in result.all()]

        if not open_symbols:
            return {"result": "PASS", "actual_value": 0, "threshold_value": corr_limit}

        # Look up correlations
        correlated_count = 0
        correlated_instruments = []

        for open_sym in open_symbols:
            open_sym = await self._normalize_symbol(open_sym)
            pair_a, pair_b = sorted([symbol, open_sym])
            corr_stmt = select(InstrumentCorrelation).where(
                InstrumentCorrelation.instrument_a == pair_a,
                InstrumentCorrelation.instrument_b == pair_b,
            )
            corr_result = await self._db.execute(corr_stmt)
            correlation = corr_result.scalar_one_or_none()

            if correlation and abs(float(correlation.correlation)) >= corr_limit:
                correlated_count += 1
                correlated_instruments.append({
                    "symbol": open_sym,
                    "correlation": float(correlation.correlation),
                })

        if correlated_count >= 2:
            return {
                "result": "FAIL",
                "actual_value": correlated_count,
                "threshold_value": corr_limit,
                "details": {"correlated_positions": correlated_instruments},
            }
        if correlated_count == 1:
            return {
                "result": "WARN",
                "actual_value": correlated_count,
                "threshold_value": corr_limit,
                "details": {"correlated_positions": correlated_instruments},
            }
        return {"result": "PASS", "actual_value": 0, "threshold_value": corr_limit}

    async def check_max_single_trade_risk(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Risk = |entry - stop| / tick_size * tick_value * quantity."""
        max_risk = settings["max_single_trade_risk"]
        enrichment = signal.enrichment_data or {}
        risk_per_contract = enrichment.get("risk_per_contract")

        if risk_per_contract is None:
            return {
                "result": "WARN",
                "actual_value": None,
                "threshold_value": max_risk,
                "details": {"reason": "No stop loss set — cannot calculate risk"},
            }

        quantity = signal.quantity or 1
        total_risk = risk_per_contract * quantity

        if total_risk > max_risk:
            return {
                "result": "FAIL",
                "actual_value": round(total_risk, 2),
                "threshold_value": max_risk,
                "details": {
                    "risk_per_contract": risk_per_contract,
                    "quantity": quantity,
                },
            }
        return {
            "result": "PASS",
            "actual_value": round(total_risk, 2),
            "threshold_value": max_risk,
        }

    async def check_trading_hours(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Check if current time falls within allowed trading hours."""
        mode = settings["trading_hours_mode"]

        if mode == "24H":
            return {"result": "PASS", "actual_value": None, "threshold_value": None}

        # Get current ET time (UTC-5 standard, UTC-4 daylight)
        # Simplified: use UTC-5 for ET approximation
        now_utc = datetime.now(UTC)
        et_offset = timedelta(hours=-5)
        now_et = now_utc + et_offset
        current_time = now_et.time()

        if mode == "RTH":
            if _RTH_START <= current_time <= _RTH_END:
                return {
                    "result": "PASS",
                    "actual_value": current_time.isoformat(),
                    "threshold_value": f"{_RTH_START.isoformat()}-{_RTH_END.isoformat()}",
                }
            return {
                "result": "FAIL",
                "actual_value": current_time.isoformat(),
                "threshold_value": f"{_RTH_START.isoformat()}-{_RTH_END.isoformat()}",
                "details": {"mode": "RTH", "reason": "Outside regular trading hours"},
            }

        if mode == "ETH":
            # ETH: 18:00 to 17:00 next day (gap is 17:00-18:00)
            if current_time >= _ETH_START or current_time <= _ETH_END:
                return {
                    "result": "PASS",
                    "actual_value": current_time.isoformat(),
                    "threshold_value": f"{_ETH_START.isoformat()}-{_ETH_END.isoformat()}",
                }
            return {
                "result": "FAIL",
                "actual_value": current_time.isoformat(),
                "threshold_value": f"{_ETH_START.isoformat()}-{_ETH_END.isoformat()}",
                "details": {"mode": "ETH", "reason": "Outside extended trading hours"},
            }

        return {"result": "PASS", "actual_value": None, "threshold_value": None}

    async def check_signal_staleness(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> dict:
        """Check if signal is too old (created_at exceeds staleness_minutes)."""
        max_age = settings["staleness_minutes"]
        age = (datetime.now(UTC) - signal.created_at.replace(tzinfo=UTC)).total_seconds()
        age_minutes = age / 60

        if age_minutes > max_age:
            return {
                "result": "FAIL",
                "actual_value": round(age_minutes, 1),
                "threshold_value": max_age,
                "details": {"reason": "Signal is too stale"},
            }
        return {
            "result": "PASS",
            "actual_value": round(age_minutes, 1),
            "threshold_value": max_age,
        }

    # ------------------------------------------------------------------
    # Risk settings CRUD
    # ------------------------------------------------------------------

    async def get_risk_settings(self, user_id: uuid.UUID) -> dict:
        """Fetch user risk settings or return defaults."""
        stmt = select(UserRiskSettings).where(
            UserRiskSettings.user_id == user_id
        )
        result = await self._db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings is None:
            return {**_DEFAULTS, "updated_at": datetime.now(UTC).isoformat()}

        return {
            "max_position_size_micro": settings.max_position_size_micro,
            "max_position_size_full": settings.max_position_size_full,
            "daily_loss_limit": float(settings.daily_loss_limit),
            "max_concurrent_positions": settings.max_concurrent_positions,
            "min_risk_reward": float(settings.min_risk_reward),
            "correlation_limit": float(settings.correlation_limit),
            "max_single_trade_risk": float(settings.max_single_trade_risk),
            "trading_hours_mode": settings.trading_hours_mode,
            "staleness_minutes": settings.staleness_minutes,
            "paper_slippage_ticks": settings.paper_slippage_ticks,
            "circuit_breaker_threshold": settings.circuit_breaker_threshold,
            "auto_flatten_loss_limit": (
                float(settings.auto_flatten_loss_limit)
                if settings.auto_flatten_loss_limit is not None
                else None
            ),
            "is_paper_mode": settings.is_paper_mode,
            "updated_at": settings.updated_at.isoformat(),
        }

    async def update_risk_settings(
        self, user_id: uuid.UUID, changes: dict
    ) -> dict:
        """Update risk settings with changelog entries."""
        stmt = select(UserRiskSettings).where(
            UserRiskSettings.user_id == user_id
        )
        result = await self._db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings is None:
            settings = UserRiskSettings(user_id=user_id)
            self._db.add(settings)
            await self._db.flush()

        # Apply changes and log each
        for key, new_value in changes.items():
            if new_value is None:
                continue
            if not hasattr(settings, key):
                continue

            old_value = getattr(settings, key)
            old_str = str(old_value) if old_value is not None else None
            new_str = str(new_value)

            if old_str == new_str:
                continue

            # Set the new value
            if isinstance(old_value, Decimal):
                setattr(settings, key, Decimal(str(new_value)))
            else:
                setattr(settings, key, new_value)

            # Create changelog entry
            changelog = RiskSettingsChangelog(
                user_id=user_id,
                setting_name=key,
                previous_value=old_str,
                new_value=new_str,
            )
            self._db.add(changelog)

        await self._db.commit()
        await self._db.refresh(settings)

        logger.info(
            "Risk settings updated",
            user_id=str(user_id),
            changed_fields=list(changes.keys()),
        )
        return await self.get_risk_settings(user_id)

    # ------------------------------------------------------------------
    # Circuit breaker
    # ------------------------------------------------------------------

    async def get_circuit_breaker_state(self, user_id: uuid.UUID) -> dict:
        """Get circuit breaker state from Redis."""
        if self._redis is None:
            return {
                "state": "CLOSED",
                "consecutive_losses": 0,
                "threshold": _DEFAULTS["circuit_breaker_threshold"],
                "last_tripped_at": None,
                "queued_signals": 0,
            }

        key = f"circuit_breaker:{user_id}"
        data = await self._redis.hgetall(key)

        settings = await self.get_risk_settings(user_id)
        threshold = settings["circuit_breaker_threshold"]

        return {
            "state": data.get("state", "CLOSED"),
            "consecutive_losses": int(data.get("consecutive_losses", 0)),
            "threshold": threshold,
            "last_tripped_at": data.get("last_tripped_at"),
            "queued_signals": int(data.get("queued_signals", 0)),
        }

    async def trip_circuit_breaker(self, user_id: uuid.UUID) -> None:
        """Set circuit breaker to TRIPPED state."""
        if self._redis is None:
            return
        key = f"circuit_breaker:{user_id}"
        await self._redis.hset(key, mapping={
            "state": "TRIPPED",
            "last_tripped_at": datetime.now(UTC).isoformat(),
        })
        logger.warning(
            "Circuit breaker tripped",
            user_id=str(user_id),
        )

    async def reset_circuit_breaker(self, user_id: uuid.UUID) -> None:
        """Reset circuit breaker to CLOSED state."""
        if self._redis is None:
            return
        key = f"circuit_breaker:{user_id}"
        await self._redis.hset(key, mapping={
            "state": "CLOSED",
            "consecutive_losses": "0",
            "queued_signals": "0",
        })
        logger.info(
            "Circuit breaker reset",
            user_id=str(user_id),
        )

    async def record_loss(self, user_id: uuid.UUID) -> bool:
        """Increment consecutive losses. Returns True if circuit breaker trips."""
        if self._redis is None:
            return False
        key = f"circuit_breaker:{user_id}"
        new_count = await self._redis.hincrby(key, "consecutive_losses", 1)

        settings = await self.get_risk_settings(user_id)
        threshold = settings["circuit_breaker_threshold"]

        if new_count >= threshold:
            await self.trip_circuit_breaker(user_id)
            return True
        return False

    async def record_win(self, user_id: uuid.UUID) -> None:
        """Reset consecutive losses on a winning trade."""
        if self._redis is None:
            return
        key = f"circuit_breaker:{user_id}"
        await self._redis.hset(key, "consecutive_losses", "0")

    # ------------------------------------------------------------------
    # Quantity calculation
    # ------------------------------------------------------------------

    async def calculate_quantity(
        self, signal: Signal, settings: dict, contract_spec: ContractSpecification
    ) -> int:
        """Calculate position size based on fixed risk per trade.

        quantity = floor(max_single_trade_risk / risk_per_contract)
        Clamped to max position size.
        """
        enrichment = signal.enrichment_data or {}
        risk_per_contract = enrichment.get("risk_per_contract")

        if risk_per_contract is None or risk_per_contract <= 0:
            return 1

        max_risk = settings["max_single_trade_risk"]
        raw_qty = math.floor(max_risk / risk_per_contract)

        # Clamp to max position size
        max_size = (
            settings["max_position_size_micro"]
            if contract_spec.is_micro
            else settings["max_position_size_full"]
        )
        return max(1, min(raw_qty, max_size))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_contract_spec(self, symbol: str) -> ContractSpecification:
        """Look up contract specification by symbol."""
        stmt = select(ContractSpecification).where(
            ContractSpecification.symbol == symbol
        )
        result = await self._db.execute(stmt)
        spec = result.scalar_one_or_none()
        if spec is None:
            raise NotFoundError("ContractSpecification", symbol)
        return spec
