"""Market data ingestion service — fetches OHLCV candle data via yfinance."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.core.logging import get_logger
from app.db.models.candle import Candle
from app.db.models.instrument import Instrument

logger = get_logger("trendedge.market_data_service")

# Yahoo Finance symbol mapping per FSD-002 Section 4.1
YAHOO_SYMBOLS: dict[str, str] = {
    "CL": "CL=F",
    "GC": "GC=F",
    "PL": "PL=F",
    "YM": "YM=F",
    "MES": "ES=F",
    "MNQ": "NQ=F",
    "SI": "SI=F",
    "HG": "HG=F",
    "NG": "NG=F",
    "ZB": "ZB=F",
}


def _download_yfinance(ticker: str, period: str, interval: str) -> dict:
    """Synchronous yfinance download — run via asyncio.to_thread."""
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        return {"rows": []}

    rows: list[dict] = []
    for ts, row in df.iterrows():
        # yfinance returns MultiIndex columns when downloading a single ticker
        # via download(); handle both flat and multi-level column shapes.
        try:
            def _val(col: str, r=row) -> float:
                v = r[col]
                return float(v.iloc[0]) if hasattr(v, "iloc") else float(v)

            o = _val("Open")
            h = _val("High")
            lo = _val("Low")
            c = _val("Close")
            vol_raw = row["Volume"]
            v = (
                int(vol_raw.iloc[0])
                if hasattr(vol_raw, "iloc")
                else int(vol_raw)
            )
        except (KeyError, IndexError, TypeError):
            continue

        # Basic OHLCV validation
        if o <= 0 or h <= 0 or lo <= 0 or c <= 0:
            continue
        if h < lo:
            continue

        rows.append({
            "timestamp": ts.to_pydatetime().replace(tzinfo=UTC),
            "open": o,
            "high": h,
            "low": lo,
            "close": c,
            "volume": max(v, 0),
        })

    return {"rows": rows}


class MarketDataService:
    """Fetches and stores OHLCV candle data from yfinance (Phase 1)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bootstrap_instrument(self, instrument_id: uuid.UUID) -> int:
        """Fetch 6 months of daily data via yfinance. Returns candle count."""
        instrument = await self._get_instrument(instrument_id)
        yahoo_symbol = instrument.yahoo_symbol or YAHOO_SYMBOLS.get(instrument.symbol)
        if not yahoo_symbol:
            raise ServiceUnavailableError(
                f"No Yahoo Finance symbol mapping for {instrument.symbol}."
            )

        logger.info(
            "Bootstrapping instrument",
            instrument_id=str(instrument_id),
            symbol=instrument.symbol,
            yahoo_symbol=yahoo_symbol,
        )

        result = await asyncio.to_thread(
            _download_yfinance, yahoo_symbol, "6mo", "1d"
        )
        rows = result["rows"]
        if not rows:
            logger.warning(
                "No candle data returned from yfinance",
                instrument_id=str(instrument_id),
                yahoo_symbol=yahoo_symbol,
            )
            return 0

        count = await self._upsert_candles(instrument_id, rows, timeframe="1D")

        # Compute ATR for all candles after bootstrap
        await self._update_atr(instrument_id, timeframe="1D")

        logger.info(
            "Bootstrap complete",
            instrument_id=str(instrument_id),
            candle_count=count,
        )
        return count

    async def ingest_latest_candles(self, instrument_id: uuid.UUID) -> int:
        """Incremental fetch of latest candles. Returns new candle count."""
        instrument = await self._get_instrument(instrument_id)
        yahoo_symbol = instrument.yahoo_symbol or YAHOO_SYMBOLS.get(instrument.symbol)
        if not yahoo_symbol:
            raise ServiceUnavailableError(
                f"No Yahoo Finance symbol mapping for {instrument.symbol}."
            )

        # Find the latest stored candle timestamp
        stmt = (
            select(Candle.timestamp)
            .where(Candle.instrument_id == instrument_id, Candle.timeframe == "1D")
            .order_by(Candle.timestamp.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        last_ts = result.scalar_one_or_none()

        # If no existing data, do a full bootstrap instead
        if last_ts is None:
            return await self.bootstrap_instrument(instrument_id)

        # Fetch last 5 days to ensure overlap and catch any gaps
        period = "5d"
        data = await asyncio.to_thread(
            _download_yfinance, yahoo_symbol, period, "1d"
        )
        rows = data["rows"]
        if not rows:
            return 0

        count = await self._upsert_candles(instrument_id, rows, timeframe="1D")

        if count > 0:
            await self._update_atr(instrument_id, timeframe="1D")

        logger.info(
            "Incremental ingest complete",
            instrument_id=str(instrument_id),
            new_candles=count,
        )
        return count

    async def detect_gaps(
        self, instrument_id: uuid.UUID, days: int = 30
    ) -> list[dict]:
        """Check for missing trading days in the last N days.

        Returns a list of gap entries: {expected_date, prev_date}.
        Note: weekends and holidays are not gaps; this is a simple
        check for consecutive-day gaps > 3 calendar days.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(Candle.timestamp)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == "1D",
                Candle.timestamp >= cutoff,
            )
            .order_by(Candle.timestamp.asc())
        )
        result = await self._db.execute(stmt)
        timestamps = [row[0] for row in result.all()]

        gaps: list[dict] = []
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i - 1]).days
            # More than 3 calendar days between trading days indicates a gap
            # (normal weekends are 2-3 days)
            if delta > 3:
                gaps.append({
                    "prev_date": timestamps[i - 1].isoformat(),
                    "next_date": timestamps[i].isoformat(),
                    "gap_calendar_days": delta,
                })

        return gaps

    @staticmethod
    def compute_atr(candles_data: list[dict], period: int = 14) -> list[float | None]:
        """Compute Wilder's smoothed ATR.

        TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
        ATR_initial = mean(TR[0:period])
        ATR_n = (ATR_{n-1} * (period-1) + TR_n) / period

        Returns list of ATR values (one per candle, None for insufficient data).
        """
        n = len(candles_data)
        if n == 0:
            return []

        atrs: list[float | None] = [None]  # First candle has no prev_close

        # Compute True Range
        trs: list[float] = []
        for i in range(1, n):
            high = float(candles_data[i]["high"])
            low = float(candles_data[i]["low"])
            prev_close = float(candles_data[i - 1]["close"])

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            trs.append(tr)

        if len(trs) < period:
            return atrs + [None] * len(trs)

        # Initial ATR is simple mean of first `period` TRs
        initial_atr = sum(trs[:period]) / period
        # Fill None for candles 1..(period-1), then the initial ATR for candle `period`
        atrs.extend([None] * (period - 1))
        atrs.append(initial_atr)

        # Wilder's smoothing for remaining candles
        current_atr = initial_atr
        for i in range(period, len(trs)):
            current_atr = (current_atr * (period - 1) + trs[i]) / period
            atrs.append(current_atr)

        return atrs

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_instrument(self, instrument_id: uuid.UUID) -> Instrument:
        """Load instrument or raise NotFoundError."""
        stmt = select(Instrument).where(Instrument.id == instrument_id)
        result = await self._db.execute(stmt)
        instrument = result.scalar_one_or_none()
        if instrument is None:
            raise NotFoundError("Instrument", str(instrument_id))
        return instrument

    async def _upsert_candles(
        self,
        instrument_id: uuid.UUID,
        rows: list[dict],
        timeframe: str,
    ) -> int:
        """Bulk upsert candles using ON CONFLICT DO UPDATE. Returns count."""
        if not rows:
            return 0

        values = [
            {
                "instrument_id": instrument_id,
                "timestamp": r["timestamp"],
                "timeframe": timeframe,
                "open": Decimal(str(r["open"])),
                "high": Decimal(str(r["high"])),
                "low": Decimal(str(r["low"])),
                "close": Decimal(str(r["close"])),
                "volume": r["volume"],
                "source": "yfinance",
            }
            for r in rows
        ]

        stmt = pg_insert(Candle).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["instrument_id", "timestamp", "timeframe"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "updated_at": datetime.now(UTC),
            },
        )
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.rowcount  # type: ignore[return-value]

    async def _update_atr(
        self, instrument_id: uuid.UUID, timeframe: str, period: int = 14
    ) -> None:
        """Compute and store ATR for all candles of an instrument."""
        stmt = (
            select(Candle)
            .where(Candle.instrument_id == instrument_id, Candle.timeframe == timeframe)
            .order_by(Candle.timestamp.asc())
        )
        result = await self._db.execute(stmt)
        candles = list(result.scalars().all())

        if len(candles) < period + 1:
            return

        candle_dicts = [
            {"high": float(c.high), "low": float(c.low), "close": float(c.close)}
            for c in candles
        ]
        atr_values = self.compute_atr(candle_dicts, period)

        for i, atr_val in enumerate(atr_values):
            if atr_val is not None and candles[i].atr_14 != Decimal(str(round(atr_val, 4))):
                candles[i].atr_14 = Decimal(str(round(atr_val, 4)))

        await self._db.commit()
