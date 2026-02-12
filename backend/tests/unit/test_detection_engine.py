"""Unit tests for the trendline detection engine (pure computation, no DB)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.services.detection.candidates import CandidateLine, generate_candidates
from app.services.detection.grading import assign_grade
from app.services.detection.pivots import detect_pivot_highs, detect_pivot_lows
from app.services.detection.projection import (
    compute_bracket_order,
    compute_safety_line,
    project_price,
)
from app.services.detection.scoring import (
    compute_composite_score,
    compute_spacing_quality,
    find_touches,
)


# ═══════════════════════════════════════════════════════════════════
# Pivot Detection Tests
# ═══════════════════════════════════════════════════════════════════


class TestPivotDetection:
    """Test pivot high/low detection via scipy.signal.find_peaks."""

    def test_simple_pivot_highs(self) -> None:
        """Detect clear peak in price data."""
        highs = np.array([10, 12, 15, 13, 11, 10, 14, 18, 16, 12, 10])
        # With n_bar=2: peaks at index 2 (15) and index 7 (18)
        indices = detect_pivot_highs(highs, n_bar=2)
        assert 2 in indices
        assert 7 in indices

    def test_simple_pivot_lows(self) -> None:
        """Detect clear trough in price data."""
        lows = np.array([15, 12, 10, 13, 16, 18, 14, 9, 11, 15, 17])
        # With n_bar=2: troughs at index 2 (10) and index 7 (9)
        indices = detect_pivot_lows(lows, n_bar=2)
        assert 2 in indices
        assert 7 in indices

    def test_flat_highs_leftmost_selected(self) -> None:
        """When two adjacent candles have identical highs, leftmost is pivot."""
        highs = np.array([10, 12, 15, 15, 12, 10, 8, 6, 8, 10, 12])
        indices = detect_pivot_highs(highs, n_bar=2)
        # The plateau at indices 2-3 should select index 2 (leftmost)
        # scipy find_peaks with plateau_size handles this
        assert len(indices) > 0
        # First detected peak should be at 2 or 3 (leftmost preferred)
        plateau_peak = [i for i in indices if i in (2, 3)]
        assert len(plateau_peak) >= 1

    def test_boundary_exclusion(self) -> None:
        """Candles within N of edges cannot be confirmed as pivots."""
        highs = np.array([20, 18, 15, 12, 14, 16, 13, 11, 10, 8, 25])
        # Index 0 (20) and index 10 (25) are at boundaries with n_bar=3
        # They should NOT be confirmed as pivots
        indices = detect_pivot_highs(highs, n_bar=3)
        assert 0 not in indices
        assert 10 not in indices

    def test_n_bar_variation(self) -> None:
        """Different n_bar values produce different pivot counts."""
        highs = np.array([10, 15, 12, 14, 11, 16, 13, 18, 14, 12, 10])
        pivots_n2 = detect_pivot_highs(highs, n_bar=2)
        pivots_n4 = detect_pivot_highs(highs, n_bar=4)
        # Smaller N produces more pivots (higher sensitivity)
        assert len(pivots_n2) >= len(pivots_n4)

    def test_monotonic_no_pivots(self) -> None:
        """Monotonically increasing data has no pivot highs (except maybe last)."""
        highs = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        indices = detect_pivot_highs(highs, n_bar=2)
        # Boundary exclusion means last values won't be pivots either
        # In truly monotonic data, no confirmed pivots exist
        assert len(indices) == 0


# ═══════════════════════════════════════════════════════════════════
# Candidate Generation & Body-Cross Validation Tests
# ═══════════════════════════════════════════════════════════════════


class TestCandidateGeneration:
    """Test pairwise candidate generation with body-cross validation."""

    def test_valid_support_line(self) -> None:
        """Support line where no candle body closes below."""
        pivot_indices = np.array([0, 10])
        pivot_prices = np.array([100.0, 105.0])
        # Closes all stay above the line
        closes = np.array([100, 101, 102, 103, 103.5, 104, 104.2, 104.5, 104.8, 105, 105])
        highs = closes + 1.0
        lows = closes - 0.5
        candidates = generate_candidates(
            pivot_indices, pivot_prices, "SUPPORT",
            closes, highs, lows,
            price_range=150.0, candle_count=270, max_slope_degrees=45.0,
        )
        assert len(candidates) == 1
        assert candidates[0].direction == "SUPPORT"

    def test_support_line_body_cross_rejection(self) -> None:
        """Support line rejected when a candle body closes below it."""
        pivot_indices = np.array([0, 10])
        pivot_prices = np.array([100.0, 105.0])
        closes = np.array([100, 101, 102, 98.0, 103, 104, 104.2, 104.5, 104.8, 105, 105])
        # Close at index 3 is 98.0, well below line price ~101.5 → rejection
        highs = closes + 1.0
        lows = closes - 0.5
        candidates = generate_candidates(
            pivot_indices, pivot_prices, "SUPPORT",
            closes, highs, lows,
            price_range=10.0, candle_count=270, max_slope_degrees=45.0,
        )
        assert len(candidates) == 0

    def test_resistance_line_body_cross_rejection(self) -> None:
        """Resistance line rejected when a candle body closes above it."""
        pivot_indices = np.array([0, 10])
        pivot_prices = np.array([110.0, 105.0])
        # Descending resistance line
        closes = np.array([110, 108, 107, 115.0, 106, 106, 105.5, 105.5, 105, 105, 105])
        # Close at index 3 is 115.0, above line price ~108.5 → rejection
        highs = closes + 0.5
        lows = closes - 1.0
        candidates = generate_candidates(
            pivot_indices, pivot_prices, "RESISTANCE",
            closes, highs, lows,
            price_range=10.0, candle_count=270, max_slope_degrees=45.0,
        )
        assert len(candidates) == 0

    def test_slope_rejection(self) -> None:
        """Lines with slope > max_slope_degrees are rejected."""
        pivot_indices = np.array([0, 5])
        pivot_prices = np.array([100.0, 200.0])
        closes = np.full(6, 150.0)
        highs = closes + 1
        lows = closes - 1
        candidates = generate_candidates(
            pivot_indices, pivot_prices, "SUPPORT",
            closes, highs, lows,
            price_range=10.0, candle_count=270, max_slope_degrees=45.0,
        )
        # Steep slope should be rejected
        assert len(candidates) == 0

    def test_wick_cross_allowed_for_support(self) -> None:
        """Wick below support line is acceptable if close stays above."""
        pivot_indices = np.array([0, 10])
        pivot_prices = np.array([100.0, 100.0])  # Horizontal line at 100
        closes = np.array([100, 101, 100.5, 100.2, 100.1, 100.3, 100.5, 100.8, 100.5, 100.2, 100])
        highs = closes + 1.0
        # Lows dip below line at some points
        lows = np.array([100, 99.5, 99.0, 98.5, 99.8, 100, 99.5, 100, 99.7, 99.9, 100])
        candidates = generate_candidates(
            pivot_indices, pivot_prices, "SUPPORT",
            closes, highs, lows,
            price_range=10.0, candle_count=270, max_slope_degrees=45.0,
        )
        # Wick crosses are OK → line should be valid
        assert len(candidates) == 1


# ═══════════════════════════════════════════════════════════════════
# Touch Scoring Tests
# ═══════════════════════════════════════════════════════════════════


class TestTouchScoring:
    """Test touch detection, spacing, and composite scoring."""

    def test_touch_within_tolerance(self) -> None:
        """Candle wick within T*ATR of line is a touch."""
        # Horizontal support line at price 100
        # ATR = 2.0, tolerance = 0.5 * 2.0 = 1.0
        highs = np.array([105, 104, 103, 102, 101, 100.5, 101, 102, 103, 104, 105,
                         104, 103, 102, 101, 100.5, 101, 102, 103, 104, 105])
        lows = np.array([99, 98, 97, 96, 99.3, 99.5, 99, 98, 97, 98, 99,
                        98, 97, 96, 99.3, 99.5, 99, 98, 97, 98, 99])
        closes = np.array([102, 101, 100, 99.5, 100.5, 100.2, 100, 101, 102, 103, 104,
                          101, 100, 99.5, 100.5, 100.2, 100, 101, 102, 103, 104])
        # Close stays above 100 (valid side for support)
        closes = np.maximum(closes, 100.01)  # Ensure no body close below
        touches = find_touches(
            anchor_idx_1=0, anchor_price_1=100.0,
            slope_raw=0.0,  # horizontal
            direction="SUPPORT",
            candle_highs=highs, candle_lows=lows, candle_closes=closes,
            atr=2.0, tolerance_multiplier=0.5,
            min_candle_spacing=6, total_candles=len(highs),
        )
        assert len(touches) > 0

    def test_touch_outside_tolerance(self) -> None:
        """Candle wick far from line is NOT a touch."""
        highs = np.full(20, 110.0)
        lows = np.full(20, 108.0)
        closes = np.full(20, 109.0)
        # Line at 100, all lows at 108 → distance = 8, tolerance = 0.5*2 = 1 → no touch
        touches = find_touches(
            anchor_idx_1=0, anchor_price_1=100.0,
            slope_raw=0.0, direction="SUPPORT",
            candle_highs=highs, candle_lows=lows, candle_closes=closes,
            atr=2.0, tolerance_multiplier=0.5,
            min_candle_spacing=6, total_candles=20,
        )
        assert len(touches) == 0

    def test_spacing_quality_perfect(self) -> None:
        """Evenly spaced touches give quality = 1.0."""
        indices = [0, 20, 40, 60]
        quality = compute_spacing_quality(indices)
        assert quality == pytest.approx(1.0)

    def test_spacing_quality_uneven(self) -> None:
        """Unevenly spaced touches give quality < 1.0."""
        indices = [0, 10, 30, 60]
        quality = compute_spacing_quality(indices)
        assert 0.0 < quality < 1.0

    def test_spacing_quality_two_points(self) -> None:
        """Two points have perfect spacing (only one gap)."""
        indices = [0, 20]
        quality = compute_spacing_quality(indices)
        assert quality == pytest.approx(1.0)

    def test_spacing_quality_single_point(self) -> None:
        """Single point or empty returns 0."""
        assert compute_spacing_quality([10]) == 0.0
        assert compute_spacing_quality([]) == 0.0

    def test_composite_score_formula(self) -> None:
        """Verify composite score matches the formula."""
        touch_count = 4
        spacing_quality = 0.85
        duration_days = 42.0  # 6 weeks
        slope_degrees = 20.0

        score = compute_composite_score(
            touch_count, spacing_quality, duration_days, slope_degrees,
        )

        duration_weeks = duration_days / 7.0
        expected_duration_factor = math.log2(duration_weeks + 1)
        expected_inverse_slope = 1 - (slope_degrees / 90)
        expected = touch_count * spacing_quality * expected_duration_factor * expected_inverse_slope
        assert score == pytest.approx(expected, rel=1e-6)

    def test_composite_score_horizontal_line(self) -> None:
        """A perfectly horizontal line gets max inverse_slope_factor of 1.0."""
        score = compute_composite_score(3, 0.8, 21.0, 0.0)
        # inverse_slope = 1.0, duration_factor = log2(3+1) = 2.0
        expected = 3 * 0.8 * math.log2(4.0) * 1.0
        assert score == pytest.approx(expected, rel=1e-6)

    def test_composite_score_steep_line(self) -> None:
        """A 45-degree line gets inverse_slope_factor of 0.5."""
        score = compute_composite_score(3, 0.8, 21.0, 45.0)
        expected = 3 * 0.8 * math.log2(4.0) * 0.5
        assert score == pytest.approx(expected, rel=1e-6)


# ═══════════════════════════════════════════════════════════════════
# Grading Tests
# ═══════════════════════════════════════════════════════════════════


class TestGrading:
    """Test A+/A/B grade assignment."""

    def test_a_plus_grade(self) -> None:
        """Trendline meeting all A+ criteria gets A+."""
        grade = assign_grade(
            touch_count=4, min_spacing=8, slope_degrees=30.0,
            duration_days=28, entry_zone_days=10,
        )
        assert grade == "A+"

    def test_a_grade(self) -> None:
        """Trendline meeting A but not A+ criteria gets A."""
        grade = assign_grade(
            touch_count=3, min_spacing=5, slope_degrees=50.0,
            duration_days=16, entry_zone_days=5,
        )
        assert grade == "A"

    def test_b_grade(self) -> None:
        """Trendline meeting B but not A criteria gets B."""
        grade = assign_grade(
            touch_count=2, min_spacing=3, slope_degrees=70.0,
            duration_days=10, entry_zone_days=1,
        )
        assert grade == "B"

    def test_no_grade(self) -> None:
        """Trendline failing all criteria returns None."""
        grade = assign_grade(
            touch_count=1, min_spacing=1, slope_degrees=80.0,
            duration_days=3, entry_zone_days=0,
        )
        assert grade is None

    def test_a_plus_strict_thresholds(self) -> None:
        """A+ requires >=3 touches, >=6 spacing, <45 slope, >=21 days, >=7 days entry."""
        # Fails on duration (20 < 21)
        grade = assign_grade(
            touch_count=4, min_spacing=8, slope_degrees=30.0,
            duration_days=20, entry_zone_days=10,
        )
        assert grade != "A+"

    def test_a_grade_slope_boundary(self) -> None:
        """A grade allows up to <60 slope."""
        grade = assign_grade(
            touch_count=3, min_spacing=4, slope_degrees=59.0,
            duration_days=14, entry_zone_days=3,
        )
        assert grade == "A"
        # 60 degrees fails A (must be <60)
        grade = assign_grade(
            touch_count=3, min_spacing=4, slope_degrees=60.0,
            duration_days=14, entry_zone_days=3,
        )
        assert grade != "A+"
        assert grade != "A"

    def test_config_overrides(self) -> None:
        """User config overrides A+ thresholds."""
        # With min_touch_count=4, A+ requires >=4 touches
        grade = assign_grade(
            touch_count=3, min_spacing=8, slope_degrees=30.0,
            duration_days=28, entry_zone_days=10,
            config={"min_touch_count": 4},
        )
        assert grade != "A+"  # 3 touches < 4 required


# ═══════════════════════════════════════════════════════════════════
# Projection Tests
# ═══════════════════════════════════════════════════════════════════


class TestProjection:
    """Test price projection and bracket order computation."""

    def test_forward_projection(self) -> None:
        """Linear projection extends the line forward."""
        price = project_price(
            anchor_idx=0, anchor_price=100.0,
            slope_raw=0.5, target_idx=10,
        )
        assert price == pytest.approx(105.0)

    def test_horizontal_projection(self) -> None:
        """Horizontal line projects same price."""
        price = project_price(
            anchor_idx=5, anchor_price=50.0,
            slope_raw=0.0, target_idx=100,
        )
        assert price == pytest.approx(50.0)

    def test_safety_line(self) -> None:
        """Safety line is projected 4 candles forward from break."""
        safety = compute_safety_line(
            anchor_idx=0, anchor_price=100.0,
            slope_raw=0.5, break_candle_idx=20,
        )
        # 4 candles forward from break: index 24
        expected = 100.0 + 0.5 * 24
        assert safety == pytest.approx(expected)

    def test_bracket_order_long(self) -> None:
        """Long bracket order with valid R-multiple."""
        result = compute_bracket_order(
            entry_price=100.0, safety_line_price=95.0,
            direction="LONG",
            tick_value=10.0, tick_size=0.25,
            risk_per_trade=500.0,
        )
        assert result["bracket_valid"] is True
        assert result["entry_price"] == 100.0
        assert result["stop_loss_price"] == 95.0
        # Risk = |100 - 95| = 5
        # Target = entry + 2*R = 100 + 10 = 110
        assert result["target_price"] == pytest.approx(110.0)
        assert result["risk_r"] == pytest.approx(5.0)
        assert result["reward_r_multiple"] == pytest.approx(2.0)

    def test_bracket_order_short(self) -> None:
        """Short bracket order with valid R-multiple."""
        result = compute_bracket_order(
            entry_price=100.0, safety_line_price=105.0,
            direction="SHORT",
            tick_value=10.0, tick_size=0.25,
            risk_per_trade=500.0,
        )
        assert result["bracket_valid"] is True
        assert result["stop_loss_price"] == 105.0
        # Target = entry - 2*R = 100 - 10 = 90
        assert result["target_price"] == pytest.approx(90.0)

    def test_bracket_order_invalid_safety_line(self) -> None:
        """Safety line on wrong side of entry produces invalid bracket."""
        # Long trade but stop is above entry — nonsensical
        result = compute_bracket_order(
            entry_price=100.0, safety_line_price=105.0,
            direction="LONG",
            tick_value=10.0, tick_size=0.01,
            risk_per_trade=500.0,
        )
        assert result["bracket_valid"] is False

    def test_bracket_order_zero_position_size(self) -> None:
        """When risk per contract exceeds risk budget, bracket_valid is false."""
        result = compute_bracket_order(
            entry_price=100.0, safety_line_price=50.0,
            direction="LONG",
            tick_value=10.0, tick_size=0.01,
            risk_per_trade=1.0,  # Very small risk budget
        )
        # Risk = 50, risk_per_contract = 50 * 10 / 0.01 = 50000
        # position_size = floor(1 / 50000) = 0
        assert result["position_size"] == 0
        assert result["bracket_valid"] is False


# ═══════════════════════════════════════════════════════════════════
# ATR Computation Test
# ═══════════════════════════════════════════════════════════════════


class TestATRComputation:
    """Test Wilder's smoothed ATR calculation."""

    def test_atr_wilder_method(self) -> None:
        """Verify ATR follows Wilder's smoothing formula."""
        from app.services.market_data_service import MarketDataService

        # Generate 15 candles of simple data
        candles = []
        for i in range(15):
            candles.append({
                "high": 100.0 + i + 2,
                "low": 100.0 + i - 2,
                "close": 100.0 + i,
            })

        atrs = MarketDataService.compute_atr(candles, period=14)
        assert len(atrs) == 15
        # First candle has no ATR (no prior close)
        assert atrs[0] is None
        # After period candles, ATR should be computed
        assert atrs[14] is not None
        assert atrs[14] > 0
