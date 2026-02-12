"""Celery tasks for market data ingestion and trendline detection."""

from __future__ import annotations

import asyncio
import uuid

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger("trendedge.trendline_tasks")


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.trendline_tasks.ingest_candles",
    queue="market_data",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def ingest_candles(self):
    """Beat schedule task: fetch latest candles for all active instruments.

    Runs 6x/day at 4H candle boundaries.
    """

    async def _run():
        from sqlalchemy import select

        from app.db.models.instrument import Instrument
        from app.db.session import AsyncSessionLocal
        from app.services.market_data_service import MarketDataService

        async with AsyncSessionLocal() as db:
            # Get all active instruments
            stmt = select(Instrument).where(Instrument.is_active == True)  # noqa: E712
            result = await db.execute(stmt)
            instruments = list(result.scalars().all())

            total_candles = 0
            for instrument in instruments:
                try:
                    svc = MarketDataService(db)
                    count = await svc.ingest_latest_candles(instrument.id)
                    total_candles += count
                    logger.info(
                        "Ingested candles",
                        instrument_id=str(instrument.id),
                        symbol=instrument.symbol,
                        count=count,
                    )
                except Exception:
                    logger.error(
                        "Failed to ingest candles for instrument",
                        instrument_id=str(instrument.id),
                        symbol=instrument.symbol,
                        exc_info=True,
                    )

            logger.info(
                "Candle ingestion batch complete",
                instrument_count=len(instruments),
                total_candles=total_candles,
            )

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error("ingest_candles task failed", exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.tasks.trendline_tasks.detect_trendlines_incremental",
    queue="detection",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def detect_trendlines_incremental(self, instrument_id: str):
    """Triggered by new candle. Runs detection for all users watching this instrument."""

    async def _run():
        from redis.asyncio import Redis
        from sqlalchemy import select

        from app.core.config import settings
        from app.db.models.user_watchlist import UserWatchlist
        from app.db.session import AsyncSessionLocal
        from app.services.trendline_service import TrendlineService

        instrument_uuid = uuid.UUID(instrument_id)

        async with AsyncSessionLocal() as db:
            redis = Redis.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
            try:
                # Find all users watching this instrument
                stmt = select(UserWatchlist.user_id).where(
                    UserWatchlist.instrument_id == instrument_uuid,
                    UserWatchlist.is_active == True,  # noqa: E712
                )
                result = await db.execute(stmt)
                user_ids = [row[0] for row in result.all()]

                for uid in user_ids:
                    try:
                        svc = TrendlineService(db, redis)
                        count = await svc.detect_trendlines(uid, instrument_uuid)
                        logger.info(
                            "Incremental detection complete",
                            user_id=str(uid),
                            instrument_id=instrument_id,
                            trendlines=count,
                        )

                        # Trigger alert evaluation for the latest candle
                        from app.db.models.candle import Candle

                        latest_stmt = (
                            select(Candle.id)
                            .where(
                                Candle.instrument_id == instrument_uuid,
                                Candle.timeframe == "1D",
                            )
                            .order_by(Candle.timestamp.desc())
                            .limit(1)
                        )
                        latest_result = await db.execute(latest_stmt)
                        latest_candle_id = latest_result.scalar_one_or_none()
                        if latest_candle_id:
                            evaluate_alerts_task.delay(
                                str(uid), instrument_id, str(latest_candle_id)
                            )
                    except Exception:
                        logger.error(
                            "Detection failed for user",
                            user_id=str(uid),
                            instrument_id=instrument_id,
                            exc_info=True,
                        )
            finally:
                await redis.aclose()

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error(
            "detect_trendlines_incremental task failed",
            instrument_id=instrument_id,
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.tasks.trendline_tasks.evaluate_alerts_task",
    queue="alerts",
    bind=True,
    max_retries=2,
    default_retry_delay=15,
)
def evaluate_alerts_task(self, user_id: str, instrument_id: str, candle_id: str):
    """Check for breaks/touches, create alert records."""

    async def _run():
        from redis.asyncio import Redis

        from app.core.config import settings
        from app.db.session import AsyncSessionLocal
        from app.services.trendline_service import TrendlineService

        async with AsyncSessionLocal() as db:
            redis = Redis.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
            try:
                svc = TrendlineService(db, redis)
                alerts = await svc.evaluate_alerts(
                    uuid.UUID(user_id),
                    uuid.UUID(instrument_id),
                    uuid.UUID(candle_id),
                )
                if alerts:
                    logger.info(
                        "Alerts generated",
                        user_id=user_id,
                        instrument_id=instrument_id,
                        alert_count=len(alerts),
                        alert_types=[a["alert_type"] for a in alerts],
                    )
            finally:
                await redis.aclose()

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error(
            "evaluate_alerts_task failed",
            user_id=user_id,
            instrument_id=instrument_id,
            candle_id=candle_id,
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.tasks.trendline_tasks.recalculate_all_trendlines",
    queue="detection",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
)
def recalculate_all_trendlines(self, user_id: str):
    """Triggered by config change. Full recalculation for user's watchlist."""

    async def _run():
        from redis.asyncio import Redis
        from sqlalchemy import select

        from app.core.config import settings
        from app.db.models.user_watchlist import UserWatchlist
        from app.db.session import AsyncSessionLocal
        from app.services.trendline_service import TrendlineService

        user_uuid = uuid.UUID(user_id)

        async with AsyncSessionLocal() as db:
            redis = Redis.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
            try:
                # Get user's active watchlist
                stmt = select(UserWatchlist.instrument_id).where(
                    UserWatchlist.user_id == user_uuid,
                    UserWatchlist.is_active == True,  # noqa: E712
                )
                result = await db.execute(stmt)
                instrument_ids = [row[0] for row in result.all()]

                total = 0
                for inst_id in instrument_ids:
                    try:
                        svc = TrendlineService(db, redis)
                        count = await svc.detect_trendlines(user_uuid, inst_id)
                        total += count
                        logger.info(
                            "Recalculated trendlines",
                            user_id=user_id,
                            instrument_id=str(inst_id),
                            trendlines=count,
                        )
                    except Exception:
                        logger.error(
                            "Recalculation failed for instrument",
                            user_id=user_id,
                            instrument_id=str(inst_id),
                            exc_info=True,
                        )

                logger.info(
                    "Full recalculation complete",
                    user_id=user_id,
                    instruments=len(instrument_ids),
                    total_trendlines=total,
                )
            finally:
                await redis.aclose()

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error(
            "recalculate_all_trendlines task failed",
            user_id=user_id,
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.tasks.trendline_tasks.bootstrap_instrument_task",
    queue="market_data",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def bootstrap_instrument_task(self, user_id: str, instrument_id: str):
    """On watchlist add: fetch historical data + run initial detection."""

    async def _run():
        from redis.asyncio import Redis

        from app.core.config import settings
        from app.db.session import AsyncSessionLocal
        from app.services.market_data_service import MarketDataService
        from app.services.trendline_service import TrendlineService

        instrument_uuid = uuid.UUID(instrument_id)
        user_uuid = uuid.UUID(user_id)

        async with AsyncSessionLocal() as db:
            # Step 1: Bootstrap market data
            market_svc = MarketDataService(db)
            candle_count = await market_svc.bootstrap_instrument(instrument_uuid)
            logger.info(
                "Bootstrap data fetched",
                user_id=user_id,
                instrument_id=instrument_id,
                candle_count=candle_count,
            )

            if candle_count == 0:
                logger.warning(
                    "No candles fetched, skipping detection",
                    instrument_id=instrument_id,
                )
                return

            # Step 2: Run initial detection
            redis = Redis.from_url(settings.UPSTASH_REDIS_URL, decode_responses=True)
            try:
                tl_svc = TrendlineService(db, redis)
                tl_count = await tl_svc.detect_trendlines(user_uuid, instrument_uuid)
                logger.info(
                    "Bootstrap detection complete",
                    user_id=user_id,
                    instrument_id=instrument_id,
                    trendlines=tl_count,
                )
            finally:
                await redis.aclose()

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error(
            "bootstrap_instrument_task failed",
            user_id=user_id,
            instrument_id=instrument_id,
            exc_info=True,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.tasks.trendline_tasks.gap_detection_and_fill",
    queue="low",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
)
def gap_detection_and_fill(self):
    """Periodic: check for missing candles and attempt to fill."""

    async def _run():
        from sqlalchemy import select

        from app.db.models.instrument import Instrument
        from app.db.session import AsyncSessionLocal
        from app.services.market_data_service import MarketDataService

        async with AsyncSessionLocal() as db:
            stmt = select(Instrument).where(Instrument.is_active == True)  # noqa: E712
            result = await db.execute(stmt)
            instruments = list(result.scalars().all())

            total_gaps = 0
            for instrument in instruments:
                try:
                    svc = MarketDataService(db)
                    gaps = await svc.detect_gaps(instrument.id, days=30)
                    if gaps:
                        total_gaps += len(gaps)
                        logger.warning(
                            "Data gaps detected",
                            instrument_id=str(instrument.id),
                            symbol=instrument.symbol,
                            gap_count=len(gaps),
                        )
                        # Attempt to fill by re-ingesting
                        await svc.ingest_latest_candles(instrument.id)
                except Exception:
                    logger.error(
                        "Gap detection failed for instrument",
                        instrument_id=str(instrument.id),
                        symbol=instrument.symbol,
                        exc_info=True,
                    )

            logger.info(
                "Gap detection batch complete",
                instrument_count=len(instruments),
                total_gaps=total_gaps,
            )

    try:
        _run_async(_run())
    except Exception as exc:
        logger.error("gap_detection_and_fill task failed", exc_info=True)
        raise self.retry(exc=exc) from exc
