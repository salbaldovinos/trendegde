"""Touch scoring, spacing quality, and composite score computation."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class TouchResult:
    """A confirmed touch on a trendline."""

    candle_index: int
    price: float
    distance_to_line: float


def find_touches(
    anchor_idx_1: int,
    anchor_price_1: float,
    slope_raw: float,
    direction: str,
    candle_highs: np.ndarray,
    candle_lows: np.ndarray,
    candle_closes: np.ndarray,
    atr: float,
    tolerance_multiplier: float = 0.5,
    min_candle_spacing: int = 6,
    total_candles: int | None = None,
    anchor_idx_2: int | None = None,
) -> list[TouchResult]:
    """Find candles that "touch" the trendline within ATR-scaled tolerance.

    FSD-002 Section 3.4.1 — a touch requires the relevant wick to be within
    the tolerance zone *and* the close to remain on the valid side of the
    line.  Anchor candles are excluded.

    Parameters
    ----------
    anchor_idx_1, anchor_price_1:
        First anchor point defining the line.
    slope_raw:
        Price-per-candle slope.
    direction:
        ``'SUPPORT'`` or ``'RESISTANCE'``.
    candle_highs, candle_lows, candle_closes:
        Full OHLC arrays.
    atr:
        Current 14-period ATR value.
    tolerance_multiplier:
        Multiplied by ATR to form the tolerance zone (default 0.5).
    min_candle_spacing:
        Minimum candle gap between consecutive qualifying touches.
    total_candles:
        End index for scanning (exclusive). Defaults to array length.
    anchor_idx_2:
        Second anchor index (excluded from touches alongside anchor_idx_1).
    """
    if total_candles is None:
        total_candles = len(candle_closes)

    tolerance = tolerance_multiplier * atr
    tol_break = 1e-4  # floating-point tolerance for "exactly on line"

    anchor_set = {anchor_idx_1}
    if anchor_idx_2 is not None:
        anchor_set.add(anchor_idx_2)

    # Scan start is right after anchor_idx_1.
    raw_touches: list[TouchResult] = []
    for idx in range(anchor_idx_1 + 1, total_candles):
        if idx in anchor_set:
            continue

        line_price = anchor_price_1 + slope_raw * (idx - anchor_idx_1)

        if direction == "SUPPORT":
            wick = float(candle_lows[idx])
            close = float(candle_closes[idx])
            # Body closed past line → break, not touch.
            if close < line_price - tol_break:
                continue
            in_zone = (line_price - tolerance) <= wick <= (line_price + tolerance)
        else:  # RESISTANCE
            wick = float(candle_highs[idx])
            close = float(candle_closes[idx])
            if close > line_price + tol_break:
                continue
            in_zone = (line_price - tolerance) <= wick <= (line_price + tolerance)

        if in_zone:
            distance = abs(wick - line_price)
            raw_touches.append(TouchResult(candle_index=idx, price=wick, distance_to_line=distance))

    # --- Spacing enforcement (FSD-002 Section 3.4.3) --------------------------
    # When two consecutive touches are closer than min_candle_spacing, keep the
    # one whose wick is closest to the line.
    if not raw_touches:
        return []

    filtered: list[TouchResult] = [raw_touches[0]]
    for touch in raw_touches[1:]:
        prev = filtered[-1]
        if touch.candle_index - prev.candle_index < min_candle_spacing:
            # Keep whichever is closer to line.
            if touch.distance_to_line < prev.distance_to_line:
                filtered[-1] = touch
        else:
            filtered.append(touch)

    return filtered


def compute_spacing_quality(touch_indices: list[int]) -> float:
    """Compute spacing quality from a list of touch candle indices.

    Includes anchor indices in the list.  Returns a value in ``[0, 1]``.

    FSD-002 Section 3.4.4:
    ``quality = 1 - (std(gaps) / mean(gaps))``, clamped to ``[0, 1]``.
    """
    if len(touch_indices) < 2:
        return 0.0

    gaps = np.diff(np.asarray(touch_indices, dtype=np.float64))

    mean_gap = float(gaps.mean())
    if mean_gap == 0.0:
        return 0.0

    std_gap = float(gaps.std(ddof=0))
    if std_gap > mean_gap:
        return 0.0

    return max(0.0, min(1.0, 1.0 - std_gap / mean_gap))


def compute_composite_score(
    touch_count: int,
    spacing_quality: float,
    duration_days: float,
    slope_degrees: float,
) -> float:
    """Compute the composite ranking score for a trendline.

    FSD-002 Section 3.6.1::

        duration_weeks = duration_days / 7
        duration_factor = log2(duration_weeks + 1)
        inverse_slope_factor = 1 - (slope_degrees / 90)
        score = touch_count * spacing_quality * duration_factor * inverse_slope_factor
    """
    duration_weeks = duration_days / 7.0
    duration_factor = math.log2(duration_weeks + 1.0)
    inverse_slope_factor = 1.0 - (min(slope_degrees, 89.99) / 90.0)
    return touch_count * spacing_quality * duration_factor * inverse_slope_factor
