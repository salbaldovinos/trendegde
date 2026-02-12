"""Quality grade assignment (A+, A, B, or None)."""

from __future__ import annotations

# Default rubric thresholds (FSD-002 Section 3.5.1).
_DEFAULT_RUBRIC: dict[str, dict[str, float]] = {
    "A+": {
        "min_touches": 3,
        "min_spacing": 6,
        "max_slope": 45.0,
        "min_duration_days": 21,
        "min_entry_zone_days": 7,
    },
    "A": {
        "min_touches": 3,
        "min_spacing": 4,
        "max_slope": 60.0,
        "min_duration_days": 14,
        "min_entry_zone_days": 3,
    },
    "B": {
        "min_touches": 2,
        "min_spacing": 3,
        "max_slope": 75.0,
        "min_duration_days": 7,
        "min_entry_zone_days": 0,
    },
}


def _build_rubric(config: dict | None) -> dict[str, dict[str, float]]:
    """Return the grading rubric, optionally adjusted by user config.

    User overrides only affect the A+ tier directly.  Lower tiers are shifted
    according to FSD-002 Section 3.5.1 specific override rules, but never
    below their original defaults.
    """
    if not config:
        return _DEFAULT_RUBRIC

    rubric: dict[str, dict[str, float]] = {
        grade: dict(thresholds) for grade, thresholds in _DEFAULT_RUBRIC.items()
    }

    if "min_touch_count" in config:
        v = config["min_touch_count"]
        rubric["A+"]["min_touches"] = v
        rubric["A"]["min_touches"] = max(3, v - 1)
        rubric["B"]["min_touches"] = max(2, v - 1)

    if "min_candle_spacing" in config:
        v = config["min_candle_spacing"]
        rubric["A+"]["min_spacing"] = v
        rubric["A"]["min_spacing"] = max(4, v - 2)
        rubric["B"]["min_spacing"] = max(3, v - 3)

    if "max_slope_degrees" in config:
        v = config["max_slope_degrees"]
        rubric["A+"]["max_slope"] = v
        rubric["A"]["max_slope"] = min(60, v + 15)
        rubric["B"]["max_slope"] = min(75, v + 30)

    if "min_duration_days" in config:
        v = config["min_duration_days"]
        rubric["A+"]["min_duration_days"] = v
        rubric["A"]["min_duration_days"] = max(14, v - 7)
        rubric["B"]["min_duration_days"] = max(7, v - 14)

    return rubric


def assign_grade(
    touch_count: int,
    min_spacing: int,
    slope_degrees: float,
    duration_days: int,
    entry_zone_days: int,
    config: dict | None = None,
) -> str | None:
    """Return ``'A+'``, ``'A'``, ``'B'``, or ``None`` (does not qualify).

    Parameters
    ----------
    touch_count:
        Number of qualifying touches (including anchors).
    min_spacing:
        Minimum gap (in candles) between any consecutive touches.
    slope_degrees:
        Normalised slope in degrees.
    duration_days:
        Calendar days from first to last touch.
    entry_zone_days:
        Calendar days from the first touch to the current candle.
    config:
        Optional user overrides.  Recognised keys:
        ``min_touch_count``, ``min_candle_spacing``,
        ``max_slope_degrees``, ``min_duration_days``.
    """
    rubric = _build_rubric(config)

    for grade in ("A+", "A", "B"):
        t = rubric[grade]
        if (
            touch_count >= t["min_touches"]
            and min_spacing >= t["min_spacing"]
            and slope_degrees < t["max_slope"]
            and duration_days >= t["min_duration_days"]
            and entry_zone_days >= t["min_entry_zone_days"]
        ):
            return grade

    return None
