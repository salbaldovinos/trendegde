"""Trendline detection pipeline orchestration and lifecycle management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.db.models.alert import Alert
from app.db.models.candle import Candle
from app.db.models.instrument import Instrument
from app.db.models.pivot import Pivot
from app.db.models.trendline import Trendline
from app.db.models.trendline_event import TrendlineEvent
from app.db.models.user_detection_config import UserDetectionConfig
from app.db.models.user_watchlist import UserWatchlist
from app.services.detection import (
    assign_grade,
    compute_composite_score,
    compute_safety_line,
    compute_spacing_quality,
    detect_pivot_highs,
    detect_pivot_lows,
    find_touches,
    generate_candidates,
    project_price,
)

logger = get_logger("trendedge.trendline_service")

# Default detection config values (must match UserDetectionConfig server defaults)
_CONFIG_DEFAULTS = {
    "min_touch_count": 3,
    "min_candle_spacing": 6,
    "max_slope_degrees": 45,
    "min_duration_days": 21,
    "touch_tolerance_atr": 0.5,
    "pivot_n_bar_lookback": 5,
    "max_lines_per_instrument": 5,
    "quiet_hours_start": None,
    "quiet_hours_end": None,
    "quiet_hours_timezone": None,
    "preset_name": None,
}

# Watchlist tier limits per FSD-002
_WATCHLIST_LIMITS: dict[str, int | None] = {
    "free": 3,
    "trader": 10,
    "pro": None,  # unlimited
    "team": None,
}

# Valid state transitions for trendlines
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "detected": {"qualifying", "invalidated"},
    "qualifying": {"active", "invalidated", "expired"},
    "active": {"qualifying", "traded", "invalidated", "expired"},
    "traded": {"invalidated"},
}


class TrendlineService:
    """Orchestrates trendline detection pipeline and lifecycle management."""

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self._db = db
        self._redis = redis

    # ------------------------------------------------------------------
    # Detection pipeline
    # ------------------------------------------------------------------

    async def detect_trendlines(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID
    ) -> int:
        """Run full detection pipeline for one instrument. Returns trendline count.

        Steps:
        1. Load user config (or defaults)
        2. Load candles for instrument
        3. Detect pivots (highs and lows)
        4. Store pivots
        5. Generate candidate lines
        6. Score touches for each candidate
        7. Grade candidates
        8. Store qualifying trendlines with state transitions
        9. Rank and surface top-N
        """
        config = await self.get_config(user_id)
        n_bar = config["pivot_n_bar_lookback"]
        min_touch = config["min_touch_count"]
        min_spacing = config["min_candle_spacing"]
        max_slope = config["max_slope_degrees"]
        min_duration = config["min_duration_days"]
        tolerance_atr = config["touch_tolerance_atr"]
        max_lines = config["max_lines_per_instrument"]

        # Load candles (daily, ordered by timestamp)
        stmt = (
            select(Candle)
            .where(Candle.instrument_id == instrument_id, Candle.timeframe == "1D")
            .order_by(Candle.timestamp.asc())
        )
        result = await self._db.execute(stmt)
        candles = list(result.scalars().all())

        if len(candles) < 2 * n_bar + 1:
            logger.info(
                "Insufficient candles for detection",
                instrument_id=str(instrument_id),
                candle_count=len(candles),
            )
            return 0

        # Build numpy arrays
        highs = np.array([float(c.high) for c in candles])
        lows = np.array([float(c.low) for c in candles])
        closes = np.array([float(c.close) for c in candles])
        price_range = float(highs.max() - lows.min())

        # Get current ATR (from the last candle that has one)
        atr_val = 0.0
        for c in reversed(candles):
            if c.atr_14 is not None:
                atr_val = float(c.atr_14)
                break
        if atr_val <= 0:
            logger.warning(
                "No valid ATR for instrument, skipping detection",
                instrument_id=str(instrument_id),
            )
            return 0

        # Detect pivots
        pivot_high_indices = detect_pivot_highs(highs, n_bar)
        pivot_low_indices = detect_pivot_lows(lows, n_bar)

        # Store pivots
        await self._store_pivots(
            instrument_id, candles, pivot_high_indices, "HIGH", n_bar
        )
        await self._store_pivots(
            instrument_id, candles, pivot_low_indices, "LOW", n_bar
        )

        # Generate and score candidates for both directions
        all_trendlines: list[dict] = []

        direction_data = [
            (
                "RESISTANCE",
                pivot_high_indices,
                highs[pivot_high_indices]
                if len(pivot_high_indices) > 0
                else np.array([]),
            ),
            (
                "SUPPORT",
                pivot_low_indices,
                lows[pivot_low_indices]
                if len(pivot_low_indices) > 0
                else np.array([]),
            ),
        ]
        for direction, pivot_indices, pivot_prices_arr in direction_data:
            if len(pivot_indices) < 2:
                continue

            candidates = generate_candidates(
                pivot_indices=pivot_indices,
                pivot_prices=pivot_prices_arr,
                direction=direction,
                candle_closes=closes,
                candle_highs=highs,
                candle_lows=lows,
                price_range=price_range,
                candle_count=len(candles),
                max_slope_degrees=max_slope,
            )

            for cand in candidates:
                anchor_price = float(pivot_prices_arr[
                    np.where(pivot_indices == cand.anchor_idx_1)[0][0]
                ])

                touches = find_touches(
                    anchor_idx_1=cand.anchor_idx_1,
                    anchor_price_1=anchor_price,
                    slope_raw=cand.slope_raw,
                    direction=direction,
                    candle_highs=highs,
                    candle_lows=lows,
                    candle_closes=closes,
                    atr=atr_val,
                    tolerance_multiplier=tolerance_atr,
                    min_candle_spacing=min_spacing,
                    anchor_idx_2=cand.anchor_idx_2,
                )

                # Total touches = 2 anchors + additional touches
                total_touches = 2 + len(touches)
                if total_touches < min_touch:
                    continue

                # Duration in days
                first_ts = candles[cand.anchor_idx_1].timestamp
                last_touch_idx = (
                    touches[-1].candle_index if touches else cand.anchor_idx_2
                )
                last_ts = candles[last_touch_idx].timestamp
                duration_days = (last_ts - first_ts).days

                if duration_days < min_duration:
                    continue

                # Scoring
                all_touch_indices = [
                    cand.anchor_idx_1,
                    cand.anchor_idx_2,
                ] + [t.candle_index for t in touches]
                spacing = compute_spacing_quality(sorted(all_touch_indices))
                score = compute_composite_score(
                    total_touches, spacing, duration_days, cand.slope_degrees
                )

                # Grading
                # Compute entry zone days (days since last touch)
                entry_zone_days = (candles[-1].timestamp - last_ts).days
                grade = assign_grade(
                    touch_count=total_touches,
                    min_spacing=min_spacing,
                    slope_degrees=cand.slope_degrees,
                    duration_days=duration_days,
                    entry_zone_days=entry_zone_days,
                    config=config,
                )

                if grade is None:
                    continue

                # Projection and safety line
                projected = project_price(
                    cand.anchor_idx_1, anchor_price, cand.slope_raw,
                    len(candles) - 1,
                )
                safety = compute_safety_line(
                    cand.anchor_idx_1, anchor_price, cand.slope_raw,
                    len(candles) - 1,
                )

                # Build touch_points JSONB
                touch_points_json = [
                    {
                        "candle_index": t.candle_index,
                        "price": round(t.price, 4),
                        "distance": round(t.distance_to_line, 4),
                        "candle_id": str(candles[t.candle_index].id),
                    }
                    for t in touches
                ]

                all_trendlines.append({
                    "candidate": cand,
                    "anchor_price": anchor_price,
                    "direction": direction,
                    "grade": grade,
                    "touch_count": total_touches,
                    "touches": touches,
                    "touch_points_json": touch_points_json,
                    "spacing_quality": spacing,
                    "composite_score": score,
                    "duration_days": duration_days,
                    "projected_price": projected,
                    "safety_line_price": safety,
                    "last_touch_at": last_ts,
                    "anchor_candle_1": candles[cand.anchor_idx_1],
                    "anchor_candle_2": candles[cand.anchor_idx_2],
                })

        # Rank by composite score and take top-N per direction
        support_lines = sorted(
            [t for t in all_trendlines if t["direction"] == "SUPPORT"],
            key=lambda x: x["composite_score"],
            reverse=True,
        )[:max_lines]
        resistance_lines = sorted(
            [t for t in all_trendlines if t["direction"] == "RESISTANCE"],
            key=lambda x: x["composite_score"],
            reverse=True,
        )[:max_lines]

        selected = support_lines + resistance_lines

        # Store trendlines
        stored_count = 0
        for tl in selected:
            cand = tl["candidate"]
            # Look up pivot IDs for anchors
            pivot_1_id = await self._find_pivot_id(
                instrument_id,
                tl["anchor_candle_1"].id,
                "HIGH" if tl["direction"] == "RESISTANCE" else "LOW",
            )
            pivot_2_id = await self._find_pivot_id(
                instrument_id,
                tl["anchor_candle_2"].id,
                "HIGH" if tl["direction"] == "RESISTANCE" else "LOW",
            )
            if pivot_1_id is None or pivot_2_id is None:
                continue

            # Determine initial status based on grade
            status = "qualifying" if tl["grade"] in ("A+", "A") else "detected"

            trendline = Trendline(
                instrument_id=instrument_id,
                user_id=user_id,
                direction=tl["direction"],
                status=status,
                grade=tl["grade"],
                anchor_pivot_1_id=pivot_1_id,
                anchor_pivot_2_id=pivot_2_id,
                slope_raw=Decimal(str(round(cand.slope_raw, 8))),
                slope_degrees=Decimal(str(round(cand.slope_degrees, 2))),
                touch_count=tl["touch_count"],
                touch_points=tl["touch_points_json"],
                spacing_quality=Decimal(str(round(tl["spacing_quality"], 3))),
                composite_score=Decimal(str(round(tl["composite_score"], 4))),
                duration_days=tl["duration_days"],
                projected_price=Decimal(str(round(tl["projected_price"], 4))),
                safety_line_price=Decimal(str(round(tl["safety_line_price"], 4))),
                last_touch_at=tl["last_touch_at"],
            )
            self._db.add(trendline)
            await self._db.flush()

            await self._log_event(
                trendline_id=trendline.id,
                event_type="state_change",
                old_value=None,
                new_value={"status": status, "grade": tl["grade"]},
                reason="Initial detection",
            )
            stored_count += 1

        await self._db.commit()

        logger.info(
            "Detection pipeline complete",
            user_id=str(user_id),
            instrument_id=str(instrument_id),
            candidates_evaluated=len(all_trendlines),
            trendlines_stored=stored_count,
        )
        return stored_count

    # ------------------------------------------------------------------
    # Trendline queries
    # ------------------------------------------------------------------

    async def get_active_trendlines(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID
    ) -> dict:
        """Query active trendlines, split by direction, ranked by proximity-adjusted score."""
        stmt = (
            select(Trendline)
            .where(
                Trendline.user_id == user_id,
                Trendline.instrument_id == instrument_id,
                Trendline.status.in_(["qualifying", "active"]),
            )
            .order_by(Trendline.composite_score.desc())
        )
        result = await self._db.execute(stmt)
        trendlines = list(result.scalars().all())

        # Fetch latest candle for proximity decay
        latest_stmt = (
            select(Candle)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == "1D",
            )
            .order_by(Candle.timestamp.desc())
            .limit(1)
        )
        latest_result = await self._db.execute(latest_stmt)
        latest_candle = latest_result.scalar_one_or_none()

        current_close = float(latest_candle.close) if latest_candle else None
        atr_val = (
            float(latest_candle.atr_14)
            if latest_candle and latest_candle.atr_14
            else None
        )

        tl_dicts: list[dict] = []
        for tl in trendlines:
            d = self._trendline_to_dict(tl)

            # Apply proximity-based score decay
            if current_close is not None and atr_val and atr_val > 0 and d.get("projected_price") is not None:
                distance = abs(d["projected_price"] - current_close)
                if distance > 5 * atr_val:
                    decay_factor = (5 * atr_val) / distance
                    d["composite_score"] = (
                        d["composite_score"] * decay_factor
                        if d["composite_score"] is not None
                        else None
                    )

            tl_dicts.append(d)

        support = sorted(
            [d for d in tl_dicts if d["direction"] == "SUPPORT"],
            key=lambda x: x.get("composite_score") or 0,
            reverse=True,
        )
        resistance = sorted(
            [d for d in tl_dicts if d["direction"] == "RESISTANCE"],
            key=lambda x: x.get("composite_score") or 0,
            reverse=True,
        )

        return {
            "support": support,
            "resistance": resistance,
            "total": len(trendlines),
        }

    async def get_trendline_detail(
        self, user_id: uuid.UUID, trendline_id: uuid.UUID
    ) -> dict | None:
        """Get single trendline with events."""
        stmt = select(Trendline).where(
            Trendline.id == trendline_id,
            Trendline.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        trendline = result.scalar_one_or_none()
        if trendline is None:
            return None

        # Load events
        events_stmt = (
            select(TrendlineEvent)
            .where(TrendlineEvent.trendline_id == trendline_id)
            .order_by(TrendlineEvent.created_at.desc())
        )
        events_result = await self._db.execute(events_stmt)
        events = list(events_result.scalars().all())

        tl_dict = self._trendline_to_dict(trendline)
        tl_dict["events"] = [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "old_value": e.old_value,
                "new_value": e.new_value,
                "reason": e.reason,
                "trigger_candle_id": str(e.trigger_candle_id) if e.trigger_candle_id else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ]
        return tl_dict

    async def dismiss_trendline(
        self, user_id: uuid.UUID, trendline_id: uuid.UUID, reason: str | None = None
    ) -> dict:
        """Transition to invalidated. Only from qualifying/active state."""
        stmt = select(Trendline).where(
            Trendline.id == trendline_id,
            Trendline.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        trendline = result.scalar_one_or_none()
        if trendline is None:
            raise NotFoundError("Trendline", str(trendline_id))

        if trendline.status not in ("qualifying", "active"):
            raise ConflictError(
                f"Cannot dismiss trendline in '{trendline.status}' state."
            )

        old_status = trendline.status
        trendline.status = "invalidated"
        trendline.invalidation_reason = reason or "User dismissed"

        await self._log_event(
            trendline_id=trendline.id,
            event_type="state_change",
            old_value={"status": old_status},
            new_value={"status": "invalidated"},
            reason=reason or "User dismissed",
        )
        await self._db.commit()

        return self._trendline_to_dict(trendline)

    # ------------------------------------------------------------------
    # State machine: promotion, demotion, expiration
    # ------------------------------------------------------------------

    async def promote_or_demote_trendlines(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID
    ) -> dict[str, int]:
        """Promote qualifying -> active or demote active -> qualifying based on proximity.

        A+ grade trendlines within 3*ATR of current price are promoted.
        Trendlines more than 3*ATR away are demoted.

        Returns {"promoted": N, "demoted": N}.
        """
        # Get latest candle for current price and ATR
        latest_stmt = (
            select(Candle)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == "1D",
            )
            .order_by(Candle.timestamp.desc())
            .limit(1)
        )
        latest_result = await self._db.execute(latest_stmt)
        latest_candle = latest_result.scalar_one_or_none()
        if latest_candle is None:
            return {"promoted": 0, "demoted": 0}

        current_close = float(latest_candle.close)
        atr_val = float(latest_candle.atr_14) if latest_candle.atr_14 else 0.0
        if atr_val <= 0:
            return {"promoted": 0, "demoted": 0}

        # Load all qualifying and active trendlines for this user+instrument
        tl_stmt = (
            select(Trendline)
            .where(
                Trendline.user_id == user_id,
                Trendline.instrument_id == instrument_id,
                Trendline.status.in_(["qualifying", "active"]),
            )
        )
        tl_result = await self._db.execute(tl_stmt)
        trendlines = list(tl_result.scalars().all())

        # Load all candles to project line prices
        candles_stmt = (
            select(Candle)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == "1D",
            )
            .order_by(Candle.timestamp.asc())
        )
        candles_result = await self._db.execute(candles_stmt)
        all_candles = list(candles_result.scalars().all())
        candle_id_to_idx = {c.id: i for i, c in enumerate(all_candles)}

        promoted = 0
        demoted = 0

        for tl in trendlines:
            # Find anchor candle index for projection
            anchor_stmt = select(Pivot).where(Pivot.id == tl.anchor_pivot_1_id)
            anchor_result = await self._db.execute(anchor_stmt)
            anchor_pivot = anchor_result.scalar_one_or_none()
            if anchor_pivot is None or anchor_pivot.candle_id not in candle_id_to_idx:
                continue

            anchor_idx = candle_id_to_idx[anchor_pivot.candle_id]
            anchor_price = float(anchor_pivot.price)
            slope = float(tl.slope_raw)
            target_idx = len(all_candles) - 1

            projected = anchor_price + slope * (target_idx - anchor_idx)
            distance = abs(projected - current_close)

            if tl.status == "qualifying" and tl.grade == "A+" and distance <= 3 * atr_val:
                old_status = tl.status
                tl.status = "active"
                await self._log_event(
                    trendline_id=tl.id,
                    event_type="state_change",
                    old_value={"status": old_status},
                    new_value={"status": "active"},
                    reason=f"Promoted: A+ grade within 3*ATR (distance={distance:.2f}, threshold={3*atr_val:.2f})",
                )
                promoted += 1

            elif tl.status == "active" and distance > 3 * atr_val:
                old_status = tl.status
                tl.status = "qualifying"
                await self._log_event(
                    trendline_id=tl.id,
                    event_type="state_change",
                    old_value={"status": old_status},
                    new_value={"status": "qualifying"},
                    reason=f"Demoted: price moved beyond 3*ATR (distance={distance:.2f}, threshold={3*atr_val:.2f})",
                )
                demoted += 1

        if promoted or demoted:
            await self._db.commit()

        logger.info(
            "Promote/demote complete",
            user_id=str(user_id),
            instrument_id=str(instrument_id),
            promoted=promoted,
            demoted=demoted,
        )
        return {"promoted": promoted, "demoted": demoted}

    async def expire_stale_trendlines(self) -> int:
        """Expire qualifying/active trendlines with last_touch_at > 6 months ago.

        Returns count of expired trendlines.
        """
        cutoff = datetime.now(UTC) - timedelta(days=180)

        stmt = (
            select(Trendline)
            .where(
                Trendline.status.in_(["qualifying", "active"]),
                Trendline.last_touch_at < cutoff,
            )
        )
        result = await self._db.execute(stmt)
        trendlines = list(result.scalars().all())

        expired_count = 0
        for tl in trendlines:
            old_status = tl.status
            tl.status = "expired"
            await self._log_event(
                trendline_id=tl.id,
                event_type="state_change",
                old_value={"status": old_status},
                new_value={"status": "expired"},
                reason=f"Expired: last touch at {tl.last_touch_at.isoformat()} exceeds 6-month threshold",
            )
            expired_count += 1

        if expired_count:
            await self._db.commit()

        logger.info(
            "Stale trendline expiration complete",
            expired_count=expired_count,
        )
        return expired_count

    # ------------------------------------------------------------------
    # User detection config
    # ------------------------------------------------------------------

    async def get_config(self, user_id: uuid.UUID) -> dict:
        """Get user detection config, create with defaults if not exists."""
        stmt = select(UserDetectionConfig).where(
            UserDetectionConfig.user_id == user_id
        )
        result = await self._db.execute(stmt)
        config = result.scalar_one_or_none()

        if config is None:
            return {**_CONFIG_DEFAULTS}

        return {
            "min_touch_count": config.min_touch_count,
            "min_candle_spacing": config.min_candle_spacing,
            "max_slope_degrees": config.max_slope_degrees,
            "min_duration_days": config.min_duration_days,
            "touch_tolerance_atr": float(config.touch_tolerance_atr),
            "pivot_n_bar_lookback": config.pivot_n_bar_lookback,
            "max_lines_per_instrument": config.max_lines_per_instrument,
            "quiet_hours_start": (
                config.quiet_hours_start.isoformat()
                if config.quiet_hours_start
                else None
            ),
            "quiet_hours_end": (
                config.quiet_hours_end.isoformat()
                if config.quiet_hours_end
                else None
            ),
            "quiet_hours_timezone": config.quiet_hours_timezone,
            "preset_name": config.preset_name,
        }

    async def update_config(self, user_id: uuid.UUID, data: dict) -> dict:
        """Update config, dispatch recalculation task."""
        stmt = select(UserDetectionConfig).where(
            UserDetectionConfig.user_id == user_id
        )
        result = await self._db.execute(stmt)
        config = result.scalar_one_or_none()

        if config is None:
            config = UserDetectionConfig(user_id=user_id)
            self._db.add(config)

        for key, value in data.items():
            if hasattr(config, key) and key != "user_id":
                setattr(config, key, value)

        await self._db.commit()
        await self._db.refresh(config)

        # Dispatch recalculation task (import here to avoid circular imports)
        try:
            from app.tasks.trendline_tasks import recalculate_all_trendlines
            recalculate_all_trendlines.delay(str(user_id))
        except Exception:
            logger.warning(
                "Failed to dispatch recalculation task",
                user_id=str(user_id),
                exc_info=True,
            )

        return await self.get_config(user_id)

    async def reset_config(self, user_id: uuid.UUID) -> dict:
        """Reset all params to defaults, dispatch recalculation."""
        stmt = select(UserDetectionConfig).where(
            UserDetectionConfig.user_id == user_id
        )
        result = await self._db.execute(stmt)
        config = result.scalar_one_or_none()

        if config is not None:
            for key, value in _CONFIG_DEFAULTS.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            await self._db.commit()

        try:
            from app.tasks.trendline_tasks import recalculate_all_trendlines
            recalculate_all_trendlines.delay(str(user_id))
        except Exception:
            logger.warning(
                "Failed to dispatch recalculation task after reset",
                user_id=str(user_id),
                exc_info=True,
            )

        return await self.get_config(user_id)

    # ------------------------------------------------------------------
    # Watchlist
    # ------------------------------------------------------------------

    async def add_to_watchlist(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID, subscription_tier: str
    ) -> dict:
        """Add instrument with tier limit enforcement."""
        # Check instrument exists
        inst_stmt = select(Instrument).where(Instrument.id == instrument_id)
        inst_result = await self._db.execute(inst_stmt)
        instrument = inst_result.scalar_one_or_none()
        if instrument is None:
            raise NotFoundError("Instrument", str(instrument_id))

        # Check tier limits
        limit = _WATCHLIST_LIMITS.get(subscription_tier)
        if limit is not None:
            count_stmt = select(func.count()).select_from(UserWatchlist).where(
                UserWatchlist.user_id == user_id,
                UserWatchlist.is_active == True,  # noqa: E712
            )
            count_result = await self._db.execute(count_stmt)
            current_count = count_result.scalar() or 0
            if current_count >= limit:
                raise ForbiddenError(
                    f"Watchlist limit of {limit} instruments "
                    f"reached for '{subscription_tier}' tier. "
                    "Upgrade your plan to add more instruments."
                )

        # Check for existing entry (may be soft-deleted)
        existing_stmt = select(UserWatchlist).where(
            UserWatchlist.user_id == user_id,
            UserWatchlist.instrument_id == instrument_id,
        )
        existing_result = await self._db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing is not None:
            if existing.is_active:
                raise ConflictError("Instrument is already on your watchlist.")
            # Reactivate soft-deleted entry
            existing.is_active = True
            await self._db.commit()
        else:
            entry = UserWatchlist(
                user_id=user_id,
                instrument_id=instrument_id,
                is_active=True,
            )
            self._db.add(entry)
            await self._db.commit()

        # Dispatch bootstrap task
        try:
            from app.tasks.trendline_tasks import bootstrap_instrument_task
            bootstrap_instrument_task.delay(str(user_id), str(instrument_id))
        except Exception:
            logger.warning(
                "Failed to dispatch bootstrap task",
                user_id=str(user_id),
                instrument_id=str(instrument_id),
                exc_info=True,
            )

        return {
            "user_id": str(user_id),
            "instrument_id": str(instrument_id),
            "symbol": instrument.symbol,
            "name": instrument.name,
            "is_active": True,
        }

    async def remove_from_watchlist(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID
    ) -> dict:
        """Soft delete (is_active=false). Retain historical data."""
        stmt = select(UserWatchlist).where(
            UserWatchlist.user_id == user_id,
            UserWatchlist.instrument_id == instrument_id,
        )
        result = await self._db.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError("Watchlist entry")

        if not entry.is_active:
            raise ConflictError("Instrument is already removed from your watchlist.")

        entry.is_active = False
        await self._db.commit()

        return {
            "user_id": str(user_id),
            "instrument_id": str(instrument_id),
            "is_active": False,
        }

    async def get_watchlist(self, user_id: uuid.UUID) -> list[dict]:
        """Get user's watchlist with instrument details."""
        stmt = (
            select(UserWatchlist, Instrument)
            .join(Instrument, UserWatchlist.instrument_id == Instrument.id)
            .where(
                UserWatchlist.user_id == user_id,
                UserWatchlist.is_active == True,  # noqa: E712
            )
            .order_by(Instrument.symbol.asc())
        )
        result = await self._db.execute(stmt)
        rows = result.all()

        return [
            {
                "instrument_id": str(wl.instrument_id),
                "symbol": inst.symbol,
                "name": inst.name,
                "exchange": inst.exchange,
                "is_active": wl.is_active,
                "added_at": wl.created_at.isoformat(),
            }
            for wl, inst in rows
        ]

    # ------------------------------------------------------------------
    # Alert evaluation
    # ------------------------------------------------------------------

    async def evaluate_alerts(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID, candle_id: uuid.UUID
    ) -> list[dict]:
        """Check for breaks/touches on qualifying/active trendlines.

        Returns list of generated alerts.
        """
        # Load the trigger candle
        candle_stmt = select(Candle).where(Candle.id == candle_id)
        candle_result = await self._db.execute(candle_stmt)
        candle = candle_result.scalar_one_or_none()
        if candle is None:
            return []

        # Load qualifying/active trendlines for this instrument + user
        tl_stmt = (
            select(Trendline)
            .where(
                Trendline.user_id == user_id,
                Trendline.instrument_id == instrument_id,
                Trendline.status.in_(["qualifying", "active"]),
            )
        )
        tl_result = await self._db.execute(tl_stmt)
        trendlines = list(tl_result.scalars().all())

        # Load all candles up to trigger candle for ATR
        candles_stmt = (
            select(Candle)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == "1D",
                Candle.timestamp <= candle.timestamp,
            )
            .order_by(Candle.timestamp.asc())
        )
        candles_result = await self._db.execute(candles_stmt)
        all_candles = list(candles_result.scalars().all())
        candle_idx_map = {c.id: i for i, c in enumerate(all_candles)}

        if candle_id not in candle_idx_map:
            return []

        trigger_idx = candle_idx_map[candle_id]
        atr_val = float(candle.atr_14) if candle.atr_14 else 0.0

        alerts: list[dict] = []

        for tl in trendlines:
            # Find anchor candle index for projection
            # Use the first anchor pivot's candle
            anchor_pivot_stmt = select(Pivot).where(Pivot.id == tl.anchor_pivot_1_id)
            anchor_result = await self._db.execute(anchor_pivot_stmt)
            anchor_pivot = anchor_result.scalar_one_or_none()
            if anchor_pivot is None or anchor_pivot.candle_id not in candle_idx_map:
                continue

            anchor_idx = candle_idx_map[anchor_pivot.candle_id]
            anchor_price = float(anchor_pivot.price)
            slope = float(tl.slope_raw)

            # Project line price at trigger candle
            line_price = anchor_price + slope * (trigger_idx - anchor_idx)
            close = float(candle.close)
            high = float(candle.high)
            low = float(candle.low)

            tolerance = 0.5 * atr_val if atr_val > 0 else 0.0
            alert_type = None

            if tl.direction == "SUPPORT":
                # Break: close below line
                if close < line_price - 1e-4:
                    alert_type = "break"
                # Touch: low within tolerance zone and close above line
                elif abs(low - line_price) <= tolerance and close >= line_price:
                    alert_type = "touch"
            else:  # RESISTANCE
                if close > line_price + 1e-4:
                    alert_type = "break"
                elif abs(high - line_price) <= tolerance and close <= line_price:
                    alert_type = "touch"

            if alert_type is None:
                continue

            alert = Alert(
                trendline_id=tl.id,
                user_id=user_id,
                alert_type=alert_type,
                direction=tl.direction,
                trigger_candle_id=candle_id,
                payload={
                    "trendline_id": str(tl.id),
                    "instrument_id": str(instrument_id),
                    "direction": tl.direction,
                    "grade": tl.grade,
                    "line_price": round(line_price, 4),
                    "trigger_close": round(close, 4),
                    "alert_type": alert_type,
                },
            )
            self._db.add(alert)
            await self._db.flush()

            # If break, invalidate the trendline
            if alert_type == "break":
                old_status = tl.status
                tl.status = "invalidated"
                tl.invalidation_reason = f"Price break at {close}"
                await self._log_event(
                    trendline_id=tl.id,
                    event_type="state_change",
                    old_value={"status": old_status},
                    new_value={"status": "invalidated"},
                    reason=f"Break detected on candle {candle_id}",
                    trigger_candle_id=candle_id,
                )

            alerts.append({
                "id": str(alert.id),
                "alert_type": alert_type,
                "direction": tl.direction,
                "trendline_id": str(tl.id),
                "grade": tl.grade,
                "line_price": round(line_price, 4),
                "trigger_close": round(close, 4),
            })

        if alerts:
            await self._db.commit()

        logger.info(
            "Alert evaluation complete",
            user_id=str(user_id),
            instrument_id=str(instrument_id),
            alerts_generated=len(alerts),
        )
        return alerts

    # ------------------------------------------------------------------
    # Event logging
    # ------------------------------------------------------------------

    async def _log_event(
        self,
        trendline_id: uuid.UUID,
        event_type: str,
        old_value: dict | None,
        new_value: dict | None,
        reason: str | None = None,
        trigger_candle_id: uuid.UUID | None = None,
    ) -> None:
        """Insert a trendline_events record."""
        event = TrendlineEvent(
            trendline_id=trendline_id,
            event_type=event_type,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            trigger_candle_id=trigger_candle_id,
        )
        self._db.add(event)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _store_pivots(
        self,
        instrument_id: uuid.UUID,
        candles: list,
        pivot_indices: np.ndarray,
        pivot_type: str,
        n_bar: int,
    ) -> None:
        """Store detected pivots, skipping duplicates."""
        for idx in pivot_indices:
            candle = candles[int(idx)]
            price = float(candle.high) if pivot_type == "HIGH" else float(candle.low)

            # Check for existing pivot at this candle
            existing_stmt = select(Pivot).where(
                Pivot.instrument_id == instrument_id,
                Pivot.candle_id == candle.id,
                Pivot.type == pivot_type,
            )
            existing_result = await self._db.execute(existing_stmt)
            if existing_result.scalar_one_or_none() is not None:
                continue

            pivot = Pivot(
                instrument_id=instrument_id,
                candle_id=candle.id,
                type=pivot_type,
                price=Decimal(str(round(price, 4))),
                timestamp=candle.timestamp,
                n_bar_lookback=n_bar,
            )
            self._db.add(pivot)

        await self._db.flush()

    async def _find_pivot_id(
        self,
        instrument_id: uuid.UUID,
        candle_id: uuid.UUID,
        pivot_type: str,
    ) -> uuid.UUID | None:
        """Find pivot ID by candle reference."""
        stmt = select(Pivot.id).where(
            Pivot.instrument_id == instrument_id,
            Pivot.candle_id == candle_id,
            Pivot.type == pivot_type,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _trendline_to_dict(tl: Trendline) -> dict:
        """Convert a Trendline ORM object to a response dict."""
        return {
            "id": str(tl.id),
            "instrument_id": str(tl.instrument_id),
            "user_id": str(tl.user_id),
            "direction": tl.direction,
            "status": tl.status,
            "grade": tl.grade,
            "slope_raw": float(tl.slope_raw),
            "slope_degrees": float(tl.slope_degrees),
            "touch_count": tl.touch_count,
            "touch_points": tl.touch_points,
            "spacing_quality": float(tl.spacing_quality) if tl.spacing_quality else None,
            "composite_score": float(tl.composite_score) if tl.composite_score else None,
            "duration_days": tl.duration_days,
            "projected_price": float(tl.projected_price) if tl.projected_price else None,
            "safety_line_price": float(tl.safety_line_price) if tl.safety_line_price else None,
            "invalidation_reason": tl.invalidation_reason,
            "last_touch_at": tl.last_touch_at.isoformat() if tl.last_touch_at else None,
            "created_at": tl.created_at.isoformat(),
            "updated_at": tl.updated_at.isoformat(),
        }
