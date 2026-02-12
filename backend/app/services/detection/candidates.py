"""Candidate trendline generation via exhaustive pairwise search."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class CandidateLine:
    """A candidate trendline connecting two pivot points."""

    anchor_idx_1: int
    anchor_idx_2: int
    direction: str  # 'SUPPORT' or 'RESISTANCE'
    slope_raw: float  # price per candle
    slope_degrees: float  # normalized degrees


def _slope_to_degrees(
    slope_raw: float,
    price_range: float,
    candle_count: int,
) -> float:
    """Convert raw slope to normalised degrees using the chart aspect ratio.

    See FSD-002 Section 3.3.3.
    """
    if candle_count == 0 or price_range == 0.0:
        return 0.0
    aspect = price_range / candle_count
    normalised = slope_raw / aspect
    return abs(math.degrees(math.atan(normalised)))


def _body_cross_check(
    anchor_idx_1: int,
    anchor_price_1: float,
    slope_raw: float,
    direction: str,
    candle_closes: np.ndarray,
) -> bool:
    """Return True if the candidate passes body-cross validation.

    FSD-002 Section 3.3.2: reject if any candle *body* (close) is on the
    wrong side of the line between the two anchors.  A close exactly on the
    line (within 0.0001 tolerance) is NOT a break.
    """
    tol = 1e-4
    for idx in range(anchor_idx_1 + 1, len(candle_closes)):
        line_price = anchor_price_1 + slope_raw * (idx - anchor_idx_1)
        close = candle_closes[idx]
        if direction == "SUPPORT":
            if close < line_price - tol:
                return False
        else:  # RESISTANCE
            if close > line_price + tol:
                return False
    return True


def generate_candidates(
    pivot_indices: np.ndarray,
    pivot_prices: np.ndarray,
    direction: str,
    candle_closes: np.ndarray,
    candle_highs: np.ndarray,
    candle_lows: np.ndarray,
    price_range: float,
    candle_count: int = 270,
    max_slope_degrees: float = 45.0,
) -> list[CandidateLine]:
    """Generate validated candidate trendlines from pairs of pivot points.

    Parameters
    ----------
    pivot_indices:
        Sorted array of candle indices for pivots of one type.
    pivot_prices:
        Prices at the corresponding pivot indices.
    direction:
        ``'SUPPORT'`` (pivot lows) or ``'RESISTANCE'`` (pivot highs).
    candle_closes / candle_highs / candle_lows:
        Full OHLC arrays for body-cross validation.
    price_range:
        High minus low over the 3-month window (for aspect ratio).
    candle_count:
        Number of candles in the standard chart window (default 270).
    max_slope_degrees:
        Reject candidates steeper than this (default 45).
    """
    n = len(pivot_indices)
    if n < 2:
        return []

    candidates: list[CandidateLine] = []

    for i in range(n):
        for j in range(i + 1, n):
            idx1 = int(pivot_indices[i])
            idx2 = int(pivot_indices[j])
            p1 = float(pivot_prices[i])
            p2 = float(pivot_prices[j])

            dx = idx2 - idx1
            if dx == 0:
                continue

            slope_raw = (p2 - p1) / dx
            slope_degrees = _slope_to_degrees(slope_raw, price_range, candle_count)

            if slope_degrees > max_slope_degrees:
                continue

            # Body-cross validation between anchors only.
            # Slice closes to [anchor1 .. anchor2] range for the check.
            segment = candle_closes[idx1 : idx2 + 1]
            if not _body_cross_check(0, p1, slope_raw, direction, segment):
                continue

            candidates.append(
                CandidateLine(
                    anchor_idx_1=idx1,
                    anchor_idx_2=idx2,
                    direction=direction,
                    slope_raw=slope_raw,
                    slope_degrees=slope_degrees,
                )
            )

    return candidates
