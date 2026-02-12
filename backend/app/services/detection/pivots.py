"""Swing point (pivot) detection using scipy.signal.find_peaks."""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks


def detect_pivot_highs(highs: np.ndarray, n_bar: int = 5) -> np.ndarray:
    """Return indices of pivot highs.

    Uses ``find_peaks`` with ``distance=n_bar``.  For flat highs (identical
    adjacent values) the leftmost candle is selected.  Boundary candles
    (within *n_bar* of either edge) are excluded because they cannot be
    confirmed.
    """
    if len(highs) < 2 * n_bar + 1:
        return np.array([], dtype=np.intp)

    peak_indices, _ = find_peaks(highs, distance=n_bar)

    # Filter: verify each peak dominates its full N-bar neighbourhood and
    # exclude boundary candles that lack sufficient context.
    confirmed: list[int] = []
    for idx in peak_indices:
        if idx < n_bar or idx >= len(highs) - n_bar:
            continue
        window = highs[idx - n_bar : idx + n_bar + 1]
        # For flat highs the peak value equals the max; leftmost wins
        # because find_peaks returns the first occurrence.
        if highs[idx] >= window.max():
            confirmed.append(idx)

    return np.array(confirmed, dtype=np.intp)


def detect_pivot_lows(lows: np.ndarray, n_bar: int = 5) -> np.ndarray:
    """Return indices of pivot lows.

    Uses ``find_peaks`` on the negated low series with ``distance=n_bar``.
    Boundary candles (within *n_bar* of either edge) are excluded.
    """
    if len(lows) < 2 * n_bar + 1:
        return np.array([], dtype=np.intp)

    # Negate so that troughs become peaks.
    peak_indices, _ = find_peaks(-lows, distance=n_bar)

    confirmed: list[int] = []
    for idx in peak_indices:
        if idx < n_bar or idx >= len(lows) - n_bar:
            continue
        window = lows[idx - n_bar : idx + n_bar + 1]
        if lows[idx] <= window.min():
            confirmed.append(idx)

    return np.array(confirmed, dtype=np.intp)
