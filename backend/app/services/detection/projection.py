"""Forward price projection, safety line, and bracket order computation."""

from __future__ import annotations

import math


def project_price(
    anchor_idx: int,
    anchor_price: float,
    slope_raw: float,
    target_idx: int,
) -> float:
    """Return the projected trendline price at *target_idx*.

    ``projected = anchor_price + slope_raw * (target_idx - anchor_idx)``
    """
    return anchor_price + slope_raw * (target_idx - anchor_idx)


def compute_safety_line(
    anchor_idx: int,
    anchor_price: float,
    slope_raw: float,
    break_candle_idx: int,
) -> float:
    """Return the safety-line price (4 candles forward from the break).

    FSD-002 Section 3.7.5: the safety line is the trendline projected 4
    candles beyond the break candle and serves as the stop-loss level.
    """
    return project_price(anchor_idx, anchor_price, slope_raw, break_candle_idx + 4)


def compute_bracket_order(
    entry_price: float,
    safety_line_price: float,
    direction: str,
    tick_value: float,
    tick_size: float,
    risk_per_trade: float,
) -> dict:
    """Compute a bracket order specification.

    Parameters
    ----------
    entry_price:
        The close that triggered the break.
    safety_line_price:
        Projected trendline price 4 candles forward (stop-loss level).
    direction:
        ``'LONG'`` or ``'SHORT'``.
    tick_value:
        Dollar value of one tick for the instrument.
    tick_size:
        Minimum price increment for the instrument.
    risk_per_trade:
        User's configured risk amount in dollars.

    Returns
    -------
    dict with keys: ``entry_price``, ``stop_loss_price``, ``target_price``,
    ``risk_r``, ``reward_r_multiple``, ``position_size``, ``bracket_valid``,
    and optionally ``reason``.
    """
    stop_loss_price = safety_line_price
    risk_r = abs(entry_price - stop_loss_price)

    # Validate stop-loss side.
    if direction == "LONG":
        valid_side = stop_loss_price < entry_price
        target_price = entry_price + 2.0 * risk_r
    else:  # SHORT
        valid_side = stop_loss_price > entry_price
        target_price = entry_price - 2.0 * risk_r

    if not valid_side:
        return {
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "target_price": target_price,
            "risk_r": risk_r,
            "reward_r_multiple": 2.0,
            "position_size": 0,
            "bracket_valid": False,
            "reason": "Safety line is on the wrong side of entry. Manual review required.",
        }

    # Position sizing: floor(risk_dollars / (R * tick_value / tick_size))
    if tick_size == 0.0 or risk_r == 0.0:
        position_size = 0
    else:
        dollar_risk_per_contract = risk_r * (tick_value / tick_size)
        position_size = (
            math.floor(risk_per_trade / dollar_risk_per_contract)
            if dollar_risk_per_contract > 0
            else 0
        )

    bracket_valid = position_size > 0

    result: dict = {
        "entry_price": entry_price,
        "stop_loss_price": stop_loss_price,
        "target_price": target_price,
        "risk_r": risk_r,
        "reward_r_multiple": 2.0,
        "position_size": position_size,
        "bracket_valid": bracket_valid,
    }

    if not bracket_valid and position_size == 0 and valid_side:
        dollar_risk_per_contract = risk_r * (tick_value / tick_size) if tick_size != 0.0 else 0.0
        result["reason"] = (
            f"Computed position size is 0 contracts. "
            f"Risk per contract (${dollar_risk_per_contract:.2f}) "
            f"exceeds configured risk limit (${risk_per_trade:.2f})."
        )

    return result
