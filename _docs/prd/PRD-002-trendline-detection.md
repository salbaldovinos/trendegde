# PRD-002: Trendline Detection Engine & Alerts

**TrendEdge -- AI-Powered Futures Trading Platform**
Feature PRD 2 of 11 | Version 1.0 | February 2026 | CONFIDENTIAL

**Status:** Draft
**Author:** TrendEdge Product
**Stakeholders:** Engineering, Trading Operations
**Last Updated:** 2026-02-11

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Data Requirements](#5-data-requirements)
6. [Dependencies on Other PRDs](#6-dependencies-on-other-prds)
7. [Testing Requirements](#7-testing-requirements)
8. [Security Considerations](#8-security-considerations)
9. [Phase Mapping](#9-phase-mapping)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. Overview & Purpose

### 1.1 Summary

The Trendline Detection Engine is TrendEdge's **signature differentiator** -- the single capability that no competitor (TradeZella, TradersPost, PickMyTrade, SignalStack) offers today. It algorithmically identifies multi-touch trendlines meeting configurable quality criteria on 4-hour futures candle data, scores and ranks them, and fires alerts when price interacts with qualifying lines.

The engine codifies the trendline methodology popularized by Tori Trades (Victoria Duke) -- 3+ touchpoints, <45 degree slope, 6+ candle spacing, 3+ weeks duration -- into a deterministic detection pipeline that runs continuously on Celery workers. This replaces the hours-per-day manual chart scanning that trendline swing traders currently perform across multiple instruments.

### 1.2 Problem Statement

Trendline-based swing traders face three core problems:

1. **Discovery is manual and time-intensive.** Scanning 5-10 instruments across multiple timeframes for qualifying multi-touch trendlines takes 1-3 hours daily. Traders miss setups on instruments they do not actively watch.

2. **Monitoring is fragile.** After identifying a trendline, the trader must set approximate price alerts in TradingView and manually verify the trendline interaction when alerted. No tool alerts on trendline-specific events (touch, break, invalidation).

3. **Quality assessment is subjective.** Two traders examining the same chart will draw different trendlines and disagree on whether a setup is "A+" grade. There is no systematic, repeatable scoring framework.

### 1.3 Solution

A server-side Python pipeline that:

- Ingests 4H OHLCV candle data for configured futures instruments
- Detects swing points (pivot highs and lows) using N-bar confirmation
- Generates and evaluates all candidate trendlines via exhaustive pair search
- Scores lines by touch count, spacing quality, slope, and duration
- Applies configurable quality filters to grade lines as A+, A, or B
- Ranks and surfaces the top 3-5 lines per instrument
- Evaluates alerts on each new 4H candle close (break, touch, new A+, invalidation)
- Routes alerts through configured notification channels
- Manages trendline lifecycle from detection through trade to invalidation

### 1.4 Success Criteria (Summary)

| Metric | Target |
|---|---|
| Detection accuracy vs. skilled manual trader | >=80% of setups identified |
| False positive rate (lines surfaced that expert would reject) | <=20% |
| Processing latency (new 4H candle to alerts delivered) | <30 seconds (p95) |
| System availability during market hours | >=99.5% |
| Zero missed candle ingestion events over 30 consecutive trading days | 0 gaps |

---

## 2. User Stories

### 2.1 Core Detection Stories

| ID | Story | Priority |
|---|---|---|
| US-TD-001 | As a trendline trader, I want the system to automatically detect multi-touch trendlines on my watched instruments so that I do not have to manually scan charts for hours each day. | P0 |
| US-TD-002 | As a trendline trader, I want to see only A+ quality trendlines (>=3 touches, proper spacing, moderate slope, sufficient duration) so that I focus on the highest-probability setups. | P0 |
| US-TD-003 | As a trendline trader, I want to receive an alert within 30 seconds of a 4H candle closing past a qualifying trendline so that I can evaluate the entry opportunity in real time. | P0 |
| US-TD-004 | As a trendline trader, I want to receive an alert when price tests a qualifying trendline (touch event) so that I can prepare for a potential break or bounce. | P0 |
| US-TD-005 | As a trendline trader, I want to be notified when a new trendline achieves A+ status so that I can add it to my watchlist before price reaches the line. | P1 |
| US-TD-006 | As a trendline trader, I want to be notified when a previously qualifying trendline is invalidated (broken without an entry opportunity) so that I can remove it from my watchlist. | P1 |

### 2.2 Configuration Stories

| ID | Story | Priority |
|---|---|---|
| US-TD-007 | As a trader, I want to configure the minimum touch count (2-5) so that I can adjust detection sensitivity to my personal strategy. | P0 |
| US-TD-008 | As a trader, I want to configure the minimum candle spacing between touches (3-20) so that I filter out trendlines with clustered touches. | P0 |
| US-TD-009 | As a trader, I want to configure the maximum slope angle (15-75 degrees) so that I exclude trendlines that are too steep for my strategy. | P1 |
| US-TD-010 | As a trader, I want to configure the minimum trendline duration (1 week to 6 months) so that I focus on trendlines with meaningful time context. | P1 |
| US-TD-011 | As a trader, I want to configure the touch tolerance (0.2-1.5x ATR) so that I control how precisely a wick must intersect the trendline to count as a touch. | P1 |
| US-TD-012 | As a trader, I want to configure pivot sensitivity (N-bar lookback: 2-10) so that I balance between detecting more swing points (noisy) and fewer (cleaner). | P1 |
| US-TD-013 | As a trader, I want to add or remove instruments from my watchlist so that the engine only scans markets I actively trade. | P0 |

### 2.3 Visualization and Review Stories

| ID | Story | Priority |
|---|---|---|
| US-TD-014 | As a trader, I want to see detected trendlines overlaid on the instrument's price chart so that I can visually verify the engine's detection quality. | P0 |
| US-TD-015 | As a trader, I want to see each trendline's metadata (touch count, slope, duration, grade, score) alongside the chart so that I can evaluate the setup. | P0 |
| US-TD-016 | As a trader, I want to manually dismiss a detected trendline so that it does not generate further alerts. | P1 |
| US-TD-017 | As a trader, I want to see a history of all trendlines detected on an instrument (active, traded, invalidated) so that I can review past setups. | P2 |
| US-TD-018 | As a trader, I want alert payloads to include the safety line price (stop loss) and the first S/R target at >=2R so that I can quickly assess the trade's risk/reward. | P0 |

### 2.4 Lifecycle Stories

| ID | Story | Priority |
|---|---|---|
| US-TD-019 | As a trader, I want the system to track that I have already traded a trendline so that it does not alert me for a second attempt on the same line (max 1 attempt per trendline per the A+ strategy). | P0 |
| US-TD-020 | As a trader, I want to see the current status of each trendline (new, active, traded, invalidated) so that I understand the trendline's lifecycle at a glance. | P1 |

---

## 3. Functional Requirements

### 3.1 Market Data Ingestion

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-001 | The system SHALL ingest historical 4H OHLCV candle data for all configured instruments from data sources sufficient to construct trendlines with a minimum of 6 months of history. | P0 |
| TD-FR-002 | The system SHALL incrementally ingest new 4H candle data within 15 seconds of candle close during market hours (Sunday 5:00 PM CT through Friday 4:00 PM CT for CME futures). | P0 |
| TD-FR-003 | The system SHALL support ingesting daily OHLCV data from yfinance as a free fallback data source for historical bootstrapping. | P0 |
| TD-FR-004 | The system SHALL support ingesting intraday (4H) OHLCV data from broker APIs (IBKR TWS, Tradovate WebSocket) as the primary real-time data source. | P0 |
| TD-FR-005 | The system SHALL detect and log gaps in candle data (missing candles due to API failures, exchange holidays, or connectivity issues) and trigger a gap-fill process automatically. | P0 |
| TD-FR-006 | The system SHALL store raw OHLCV data in PostgreSQL with instrument identifier, timestamp, open, high, low, close, volume, and data source fields. | P0 |
| TD-FR-007 | The system SHALL deduplicate candle data on (instrument, timestamp) to prevent double-counting from multiple data sources. | P0 |
| TD-FR-008 | The system SHALL compute the 14-period ATR (Average True Range) for each instrument on 4H candles, updated with each new candle, and store it for use in touch tolerance calculations. | P0 |

### 3.2 Swing Point Detection

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-010 | The system SHALL identify pivot highs using N-bar confirmation: a candle whose high is greater than or equal to the highs of the N candles before and after it. Default N=5. | P0 |
| TD-FR-011 | The system SHALL identify pivot lows using N-bar confirmation: a candle whose low is less than or equal to the lows of the N candles before and after it. Default N=5. | P0 |
| TD-FR-012 | The system SHALL support Williams Fractals (N=2) as a higher-sensitivity alternative pivot detection method, selectable per user configuration. | P1 |
| TD-FR-013 | The system SHALL use `scipy.signal.find_peaks` (or equivalent) for efficient pivot detection, with the `distance` parameter mapped to the user's N-bar lookback setting. | P0 |
| TD-FR-014 | The system SHALL store detected pivot points with their type (high/low), timestamp, price, and the N-bar lookback value used for detection. | P0 |
| TD-FR-015 | The system SHALL re-evaluate pivots incrementally when new candles arrive, rather than recomputing all pivots from scratch, except during full recalculation events. | P1 |
| TD-FR-016 | The system SHALL allow the user to configure the N-bar lookback parameter within the range of 2-10, with a default of 5. | P0 |

### 3.3 Candidate Line Generation

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-020 | The system SHALL generate candidate trendlines by connecting all valid pairs of pivot points of the same type (high-to-high for resistance lines, low-to-low for support lines). | P0 |
| TD-FR-021 | The system SHALL evaluate N x (N-1) / 2 candidate lines for each pivot type (highs and lows separately) using exhaustive pairwise search. | P0 |
| TD-FR-022 | The system SHALL apply RANSAC (Random Sample Consensus) fitting as an alternative to exhaustive search when the number of pivot points exceeds a configurable threshold (default: 50 pivots) to maintain computational efficiency. | P1 |
| TD-FR-023 | The system SHALL reject candidate lines where any candle body (not wick) between the anchor points closes on the wrong side of the line (i.e., a support line with a candle body closing below it, or a resistance line with a candle body closing above it). This validates the line has not been broken in its history. | P0 |
| TD-FR-024 | The system SHALL compute the slope of each candidate line in degrees, normalized to a standard chart aspect ratio (3-month window at standard display dimensions), to ensure slope comparisons are meaningful across instruments with different price scales. | P0 |
| TD-FR-025 | The system SHALL extend each candidate line forward from the last anchor point to the current candle to determine the current projected price level for alert evaluation. | P0 |
| TD-FR-026 | The system SHALL store candidate lines with their anchor points (pivot pair), slope, projected current price, and direction (support/resistance). | P0 |

### 3.4 Touch Scoring System

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-030 | The system SHALL count "touches" as additional pivot points (beyond the two anchor points) whose wicks fall within the ATR-scaled tolerance zone of the trendline. | P0 |
| TD-FR-031 | A touch SHALL be defined as a candle whose wick (high for resistance lines, low for support lines) intersects the trendline within a tolerance of T x ATR, where T is user-configurable (default: 0.5, range: 0.2-1.5). | P0 |
| TD-FR-032 | The system SHALL use the 14-period ATR computed at the time of each candidate touch candle (not the current ATR) for historically accurate touch scoring. | P1 |
| TD-FR-033 | The system SHALL NOT count candle bodies that pass through the line as touches; only wick-to-line interactions qualify. A body crossing the line indicates a break, not a touch. | P0 |
| TD-FR-034 | The system SHALL compute a spacing quality score for each trendline, measuring the regularity of candle gaps between consecutive touches. Evenly-spaced touches score higher than clustered touches. Formula: spacing_quality = 1 - (std_dev(gaps) / mean(gaps)), where gaps are measured in 4H candle count between consecutive touches. | P0 |
| TD-FR-035 | The system SHALL require a minimum number of candles between consecutive touches, configurable by the user (default: 6, range: 3-20). Touch pairs with fewer candles between them than the minimum SHALL be collapsed to a single touch (the one closest to the line). | P0 |
| TD-FR-036 | The system SHALL record the candle index and price of each qualifying touch for display on the chart overlay. | P0 |

### 3.5 Quality Filtering and Grading

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-040 | The system SHALL assign a quality grade to each candidate trendline based on the following grading rubric: | P0 |

**Grading Rubric:**

| Grade | Touch Count | Min Candle Spacing | Max Slope | Min Duration | Entry Zone |
|---|---|---|---|---|---|
| A+ | >=3 | >=6 candles | <45 degrees | >=3 weeks from 1st touch | >=1 week from 1st touch to current price zone |
| A | >=3 | >=4 candles | <60 degrees | >=2 weeks from 1st touch | >=3 days from 1st touch to current price zone |
| B | >=2 | >=3 candles | <75 degrees | >=1 week from 1st touch | No minimum |

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-041 | The system SHALL filter out candidate trendlines that do not meet at least B grade criteria. Lines below B grade SHALL NOT be stored or surfaced. | P0 |
| TD-FR-042 | The system SHALL apply the user's configured parameter overrides (touch count, spacing, slope, duration) when evaluating grade criteria. If a user sets min touch count to 4, then A+ requires >=4 touches instead of the default >=3. | P0 |
| TD-FR-043 | The system SHALL evaluate the entry zone requirement: for A+ grade, the current projected price must be at least 1 week of price action away from the first touch point, ensuring the trendline has meaningful duration before the trader engages. | P0 |
| TD-FR-044 | The system SHALL reject trendlines where the line has been previously broken by a candle body close on the wrong side, even if price subsequently returned. Once broken, a line is invalidated permanently. | P0 |
| TD-FR-045 | The system SHALL recompute grades when user configuration changes, promoting or demoting trendlines as appropriate, and firing alerts for newly qualified A+ lines. | P1 |

### 3.6 Trendline Ranking and Surfacing

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-050 | The system SHALL compute a composite score for each qualifying trendline using the formula: `score = touch_count * spacing_quality * duration_factor * inverse_slope_factor`. | P0 |
| TD-FR-051 | The `duration_factor` SHALL be computed as `log2(duration_in_weeks + 1)`, providing diminishing returns for very old trendlines while still rewarding longer-lived lines over short-lived ones. | P0 |
| TD-FR-052 | The `inverse_slope_factor` SHALL be computed as `1 - (slope_degrees / 90)`, rewarding flatter (more horizontal) trendlines which historically produce higher-probability setups. | P0 |
| TD-FR-053 | The system SHALL surface the top 3-5 trendlines per instrument, ranked by composite score, to the user's dashboard and alert pipeline. The exact count SHALL be configurable (default: 5, range: 1-10). | P0 |
| TD-FR-054 | The system SHALL surface both support and resistance trendlines independently, maintaining separate top-N lists for each direction. | P0 |
| TD-FR-055 | The system SHALL deprioritize (but not remove) trendlines that are far from current price (projected trendline price more than 5x ATR from current price), as these are unlikely to generate near-term trading opportunities. | P1 |
| TD-FR-056 | The system SHALL recalculate rankings on each new 4H candle close, as new candles may add touches, change spacing metrics, or bring price closer to a trendline. | P0 |

### 3.7 Alert Generation and Routing

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-060 | The system SHALL generate a **Trendline Break** alert when a 4H candle closes past a qualifying trendline (close price crosses the projected line level). For support lines, the close must be below the line; for resistance lines, the close must be above the line. | P0 |
| TD-FR-061 | The system SHALL generate a **Trendline Touch** alert when a candle's wick comes within the touch tolerance (default 0.5x ATR) of a qualifying trendline without a body close past the line. | P0 |
| TD-FR-062 | The system SHALL generate a **New A+ Trendline** alert when a trendline's grade is promoted to A+ (either through a new touch qualifying it or through a change in duration crossing the threshold). | P1 |
| TD-FR-063 | The system SHALL generate a **Trendline Invalidated** alert when a previously qualifying trendline is broken by a candle body close without the trader having entered a trade on that line. | P1 |
| TD-FR-064 | Each alert payload SHALL include: instrument, direction (long/short), trendline grade, touch count, slope, duration, projected line price at current candle, safety line price (stop loss at 4th candle projection), first S/R target at >=2R, current ATR, alert type, and timestamp. | P0 |
| TD-FR-065 | The system SHALL route alerts to the user's configured notification channels: Telegram (P0), email (P1), Discord (P1), push notification (P2), and WebSocket push to the dashboard (P0). | P0 |
| TD-FR-066 | The system SHALL NOT generate duplicate alerts for the same trendline event. A break alert for trendline X on instrument Y SHALL fire exactly once. Subsequent candles past the line SHALL NOT re-trigger the break alert. | P0 |
| TD-FR-067 | The system SHALL include a unique `trendline_id` and `alert_id` in each alert payload to enable downstream systems (execution pipeline, journal) to link trades back to specific trendlines. | P0 |
| TD-FR-068 | The system SHALL support alert suppression during configurable quiet hours (e.g., overnight session 8:00 PM - 6:00 AM local time) with alerts queued and delivered at the end of the quiet period. | P2 |
| TD-FR-069 | Break alert payloads SHALL include a pre-computed bracket order specification: entry price (candle close), stop loss price (safety line at 4th candle), take profit price (first S/R level at >=2R), and computed position size based on the user's configured risk per trade. | P0 |

### 3.8 Trendline Lifecycle Management

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-070 | The system SHALL track each trendline through a defined lifecycle with the following states: `detected` --> `qualifying` --> `active` --> `traded` --> `invalidated` (or `expired`). | P0 |
| TD-FR-071 | A trendline enters `detected` state when the candidate line generation algorithm identifies it for the first time. | P0 |
| TD-FR-072 | A trendline transitions from `detected` to `qualifying` when it meets at least B grade criteria. | P0 |
| TD-FR-073 | A trendline transitions from `qualifying` to `active` when it meets A+ grade criteria and price is within actionable range (projected line price within 3x ATR of current price). | P0 |
| TD-FR-074 | A trendline transitions from `active` to `traded` when a trade is entered on that trendline (linked via signal/trade system). Per the A+ strategy, a trendline SHALL only support one trade attempt. | P0 |
| TD-FR-075 | A trendline transitions to `invalidated` when a candle body closes past the line without the trader having entered (the setup was missed or deliberately skipped). | P0 |
| TD-FR-076 | A trendline transitions to `expired` when it has been in `qualifying` or `active` state for longer than 6 months without price interaction, indicating the market has moved away from the line. | P2 |
| TD-FR-077 | The system SHALL persist the full lifecycle history of each trendline, including state transition timestamps and trigger events, for analytics and backtesting purposes. | P1 |
| TD-FR-078 | The system SHALL allow a user to manually dismiss a trendline (transition to `invalidated` with reason "user_dismissed"), preventing further alerts on that line. | P1 |

### 3.9 Configuration Management

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-080 | The system SHALL store detection configuration per user, allowing each user to have independent parameter settings. | P0 |
| TD-FR-081 | The system SHALL provide the following configurable parameters with their defaults and valid ranges: | P0 |

| Parameter | Default | Min | Max | Unit |
|---|---|---|---|---|
| Minimum touch count | 3 | 2 | 5 | count |
| Minimum candle spacing between touches | 6 | 3 | 20 | 4H candles |
| Maximum slope angle | 45 | 15 | 75 | degrees |
| Minimum trendline duration | 3 weeks | 1 week | 6 months | time |
| Touch tolerance | 0.5 | 0.2 | 1.5 | x ATR |
| Pivot sensitivity (N-bar lookback) | 5 | 2 | 10 | bars |
| Max trendlines surfaced per instrument | 5 | 1 | 10 | count |
| Alert quiet hours start | disabled | -- | -- | local time |
| Alert quiet hours end | disabled | -- | -- | local time |

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-082 | The system SHALL validate all parameter changes against the valid ranges and reject out-of-range values with a descriptive error message. | P0 |
| TD-FR-083 | The system SHALL trigger a full recalculation of trendlines for the user's watched instruments when detection parameters change, completing within 60 seconds. | P1 |
| TD-FR-084 | The system SHALL support a "Reset to Defaults" action that restores all parameters to the Tori Trades A+ strategy defaults. | P1 |
| TD-FR-085 | The system SHALL support named configuration presets (e.g., "Tori A+ Strict", "High Sensitivity", "Conservative") that users can save and switch between. | P2 |

### 3.10 Instrument Management

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-090 | The system SHALL support the following Phase 1 instruments: Platinum (PL), Crude Oil (CL), Gold (GC), Dow (YM), Micro E-mini S&P 500 (MES), Micro E-mini Nasdaq (MNQ). | P0 |
| TD-FR-091 | The system SHALL allow users to add or remove instruments from their personal watchlist, subject to tier limits (Free: 3, Trader: 10, Pro/Team: unlimited). | P0 |
| TD-FR-092 | Adding an instrument to a user's watchlist SHALL trigger a historical data fetch and initial trendline detection run for that instrument, completing within 2 minutes. | P0 |
| TD-FR-093 | Removing an instrument from a user's watchlist SHALL stop alert generation for that instrument but SHALL NOT delete historical trendline data (data is retained for analytics). | P1 |
| TD-FR-094 | The system SHALL display each instrument with its full name, ticker symbol, exchange, tick size, tick value, and current continuous contract month. | P0 |

### 3.11 Continuous Contract Symbol Mapping

| ID | Requirement | Priority |
|---|---|---|
| TD-FR-100 | The system SHALL maintain a mapping of each instrument's generic continuous symbol to its current front-month contract (e.g., CL -> CLH26 for March 2026 Crude Oil). | P0 |
| TD-FR-101 | The system SHALL track contract expiration dates and roll dates for each instrument, using first-notice-day-minus-N (configurable, default N=3 trading days) as the roll trigger. | P0 |
| TD-FR-102 | The system SHALL handle contract rollovers by: (a) switching data ingestion to the new front-month contract, (b) applying a price adjustment (back-adjustment or ratio adjustment, configurable) to maintain a continuous price series, and (c) recalculating all active trendlines against the adjusted series. | P0 |
| TD-FR-103 | The system SHALL map TradingView-style continuous symbols (NQ1!, ES1!, CL1!) to the appropriate broker-specific contract symbols (IBKR: NQ + expiry, Tradovate: NQH6) when routing signals to the execution pipeline. | P0 |
| TD-FR-104 | The system SHALL store the roll adjustment factor for each contract transition, enabling accurate historical price reconstruction for backtesting. | P1 |
| TD-FR-105 | The system SHALL support both back-adjusted (additive offset) and ratio-adjusted (multiplicative factor) continuous contract methods, configurable per instrument. Default: back-adjusted. | P2 |

**CME Futures Contract Specifications (Phase 1):**

| Instrument | Symbol | Exchange | Tick Size | Tick Value | Typical Roll | Micro Variant |
|---|---|---|---|---|---|---|
| Platinum | PL | NYMEX | 0.10 | $5.00 | 3rd-to-last business day | -- |
| Crude Oil | CL | NYMEX | 0.01 | $10.00 | 3 days before 25th of prior month | MCL |
| Gold | GC | COMEX | 0.10 | $10.00 | Last trade day -2 of delivery month | MGC |
| E-mini Dow | YM | CBOT | 1.00 | $5.00 | 3rd Friday of expiry month | MYM |
| Micro E-mini S&P | MES | CME | 0.25 | $1.25 | 3rd Friday of expiry month | -- |
| Micro E-mini Nasdaq | MNQ | CME | 0.25 | $0.50 | 3rd Friday of expiry month | -- |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Target | Priority |
|---|---|---|---|
| TD-NFR-001 | End-to-end latency from 4H candle close to alert delivery (Telegram/WebSocket) | <30 seconds (p95) | P0 |
| TD-NFR-002 | Candle ingestion latency from broker API to database write | <15 seconds (p95) | P0 |
| TD-NFR-003 | Full trendline recalculation for a single instrument (6 months of 4H data, ~600 candles) | <10 seconds | P0 |
| TD-NFR-004 | Full trendline recalculation for all Phase 1 instruments (6 instruments) | <30 seconds (parallel processing) | P0 |
| TD-NFR-005 | Incremental trendline update on new candle (evaluate existing lines + check for new pivots) | <5 seconds per instrument | P0 |
| TD-NFR-006 | Dashboard trendline overlay rendering (fetch + draw lines on chart) | <2 seconds (p95) | P1 |
| TD-NFR-007 | User configuration change to full recalculation completion | <60 seconds | P1 |

### 4.2 Accuracy

| ID | Requirement | Target | Priority |
|---|---|---|---|
| TD-NFR-010 | Detection accuracy: percentage of A+ setups identified by engine that a skilled manual trader would also identify | >=80% | P0 |
| TD-NFR-011 | False positive rate: percentage of surfaced A+ trendlines that an expert reviewer would reject as non-qualifying | <=20% | P0 |
| TD-NFR-012 | Touch accuracy: percentage of algorithmically counted touches that match manual expert count | >=90% | P0 |
| TD-NFR-013 | Break detection accuracy: percentage of valid 4H close breaks correctly identified | >=99% (near-deterministic, as this is a simple close vs. line comparison) | P0 |
| TD-NFR-014 | False break suppression: percentage of wick-only crosses (not body closes) correctly classified as non-breaks | 100% (deterministic) | P0 |

### 4.3 Scalability

| ID | Requirement | Target | Priority |
|---|---|---|---|
| TD-NFR-020 | Phase 1 capacity: simultaneous instruments under detection | 6-10 instruments | P0 |
| TD-NFR-021 | Phase 2 capacity: simultaneous instruments under detection | 50 instruments | P1 |
| TD-NFR-022 | Phase 3 capacity: simultaneous instruments under detection | 200+ instruments | P2 |
| TD-NFR-023 | User scalability: concurrent users with independent configurations | Phase 1: 1, Phase 2: 100, Phase 3: 1,000+ | P0/P1/P2 |
| TD-NFR-024 | Celery worker horizontal scaling: adding workers SHALL linearly reduce processing time per instrument batch | Linear scaling to 8 workers | P1 |
| TD-NFR-025 | Database query performance: trendline queries per instrument SHALL complete in <100ms regardless of total trendline count in the system | <100ms | P1 |

### 4.4 Reliability

| ID | Requirement | Target | Priority |
|---|---|---|---|
| TD-NFR-030 | System availability during CME market hours (Sunday 5 PM CT - Friday 4 PM CT) | >=99.5% | P0 |
| TD-NFR-031 | Zero missed 4H candle ingestion events over 30 consecutive trading days | 0 missed | P0 |
| TD-NFR-032 | Alert delivery success rate (at least one channel delivers successfully) | >=99.9% | P0 |
| TD-NFR-033 | Automatic recovery from transient data source failures (broker API timeout) within 3 retry attempts | 3 retries, exponential backoff | P0 |
| TD-NFR-034 | Celery worker crash recovery: failed tasks automatically re-queued and retried | Auto-retry with dead-letter queue after 3 failures | P0 |
| TD-NFR-035 | Data consistency: no partial writes to trendline state (all updates within a single database transaction) | ACID compliant | P0 |

### 4.5 Observability

| ID | Requirement | Target | Priority |
|---|---|---|---|
| TD-NFR-040 | Structured logging for all pipeline stages (ingestion, detection, scoring, alerting) with correlation IDs | Every pipeline run | P0 |
| TD-NFR-041 | Metrics collection: processing time per stage, candle count, pivot count, candidate count, qualifying line count, alert count | Per pipeline run | P0 |
| TD-NFR-042 | Alerting on pipeline failures: Telegram/PagerDuty notification if any 4H candle processing cycle fails | Within 1 minute of failure | P0 |
| TD-NFR-043 | Dashboard showing engine health: last successful run, processing times, error rates, data freshness | Real-time | P1 |

---

## 5. Data Requirements

### 5.1 OHLCV Data Sources

| Source | Data Type | Instruments | Cost | Latency | Priority |
|---|---|---|---|---|---|
| yfinance | Daily OHLCV (historical) | All CME futures via Yahoo Finance tickers (CL=F, GC=F, PL=F, YM=F, ES=F, NQ=F) | Free | End of day | P0 (bootstrap) |
| Interactive Brokers TWS API | 4H OHLCV (historical + real-time) | All Phase 1 instruments via contract specification | $10-25/mo (CME data subscription) | <5 seconds | P0 (primary) |
| Tradovate WebSocket API | 4H OHLCV (historical + real-time) | All Phase 1 instruments | Included with funded account | <5 seconds | P0 (alternative) |
| Nasdaq Data Link (Quandl) | Daily continuous contract data | CME futures (SCF/CME dataset) | Free tier available | End of day | P1 (reference) |
| Databento | Tick/minute historical data | All CME instruments | $125 free credit, then per-query | On-demand | P2 (backtesting) |

### 5.2 Data Storage Schema

**Table: `candles`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| instrument_id | UUID | FK to instruments table |
| timestamp | TIMESTAMPTZ | Candle open timestamp (UTC) |
| timeframe | VARCHAR(4) | Candle timeframe ('4H', '1D', '1W') |
| open | DECIMAL(12,4) | Open price |
| high | DECIMAL(12,4) | High price |
| low | DECIMAL(12,4) | Low price |
| close | DECIMAL(12,4) | Close price |
| volume | BIGINT | Volume |
| source | VARCHAR(20) | Data source identifier |
| created_at | TIMESTAMPTZ | Record creation timestamp |
| UNIQUE | | (instrument_id, timestamp, timeframe) |

**Table: `instruments`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| symbol | VARCHAR(10) | Generic symbol (CL, GC, PL, etc.) |
| name | VARCHAR(100) | Full name (Crude Oil, Gold, etc.) |
| exchange | VARCHAR(10) | Exchange (NYMEX, COMEX, CBOT, CME) |
| tick_size | DECIMAL(8,4) | Minimum price increment |
| tick_value | DECIMAL(8,2) | Dollar value per tick |
| current_contract | VARCHAR(10) | Current front-month contract symbol |
| roll_date | DATE | Next contract roll date |
| is_active | BOOLEAN | Whether instrument is available for detection |
| contract_months | VARCHAR(24) | Valid contract months (e.g., 'FGHJKMNQUVXZ') |

**Table: `pivots`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| instrument_id | UUID | FK to instruments |
| candle_id | UUID | FK to candles |
| type | VARCHAR(4) | 'HIGH' or 'LOW' |
| price | DECIMAL(12,4) | Pivot price (high or low of candle) |
| timestamp | TIMESTAMPTZ | Candle timestamp |
| n_bar_lookback | INTEGER | N-bar confirmation value used |
| created_at | TIMESTAMPTZ | Detection timestamp |

**Table: `trendlines`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| instrument_id | UUID | FK to instruments |
| user_id | UUID | FK to users (owner) |
| direction | VARCHAR(10) | 'SUPPORT' or 'RESISTANCE' |
| anchor_pivot_1_id | UUID | FK to pivots (first anchor) |
| anchor_pivot_2_id | UUID | FK to pivots (second anchor) |
| slope | DECIMAL(8,4) | Slope in degrees |
| slope_raw | DECIMAL(16,8) | Slope in price/candle units |
| touch_count | INTEGER | Total qualifying touches (including anchors) |
| touch_points | JSONB | Array of {pivot_id, candle_id, price, timestamp} |
| spacing_quality | DECIMAL(4,3) | 0.0-1.0 score |
| duration_days | INTEGER | Calendar days from first to last touch |
| grade | VARCHAR(2) | 'A+', 'A', or 'B' |
| composite_score | DECIMAL(8,4) | Ranking score |
| status | VARCHAR(15) | 'detected', 'qualifying', 'active', 'traded', 'invalidated', 'expired' |
| projected_price | DECIMAL(12,4) | Current projected price on the line |
| safety_line_price | DECIMAL(12,4) | Stop loss price (4th candle projection) |
| target_price | DECIMAL(12,4) | First S/R at >=2R |
| config_snapshot | JSONB | User config at time of detection |
| created_at | TIMESTAMPTZ | First detection timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |
| status_changed_at | TIMESTAMPTZ | Last state transition timestamp |

**Table: `trendline_events`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| trendline_id | UUID | FK to trendlines |
| event_type | VARCHAR(20) | 'state_change', 'touch_added', 'grade_change', 'score_update' |
| old_value | JSONB | Previous state/value |
| new_value | JSONB | New state/value |
| trigger_candle_id | UUID | FK to candles that caused the event |
| created_at | TIMESTAMPTZ | Event timestamp |

**Table: `alerts`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| trendline_id | UUID | FK to trendlines |
| alert_type | VARCHAR(30) | 'break', 'touch', 'new_a_plus', 'invalidated' |
| payload | JSONB | Full alert data (instrument, prices, targets, etc.) |
| channels_sent | JSONB | Array of {channel, status, timestamp} |
| created_at | TIMESTAMPTZ | Alert generation timestamp |
| acknowledged_at | TIMESTAMPTZ | User acknowledgment timestamp |

**Table: `user_detection_config`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users (unique) |
| min_touch_count | INTEGER | Default 3 |
| min_candle_spacing | INTEGER | Default 6 |
| max_slope_degrees | INTEGER | Default 45 |
| min_duration_days | INTEGER | Default 21 (3 weeks) |
| touch_tolerance_atr | DECIMAL(3,1) | Default 0.5 |
| pivot_n_bar_lookback | INTEGER | Default 5 |
| max_lines_per_instrument | INTEGER | Default 5 |
| quiet_hours_start | TIME | Nullable |
| quiet_hours_end | TIME | Nullable |
| quiet_hours_timezone | VARCHAR(50) | Nullable |
| preset_name | VARCHAR(50) | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Table: `user_watchlist`**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| instrument_id | UUID | FK to instruments |
| added_at | TIMESTAMPTZ | When instrument was added |
| is_active | BOOLEAN | Whether detection is running |
| UNIQUE | | (user_id, instrument_id) |

### 5.3 Data Retention Policies

| Data Type | Retention Period | Storage Tier |
|---|---|---|
| Raw 4H OHLCV candles | Indefinite (required for trendline recalculation) | PostgreSQL primary |
| Daily OHLCV candles | Indefinite | PostgreSQL primary |
| Pivot points | Indefinite | PostgreSQL primary |
| Active trendlines | Indefinite while in active states | PostgreSQL primary |
| Invalidated/expired trendlines | 2 years (then archived) | PostgreSQL primary, then cold storage |
| Trendline events (audit log) | 1 year | PostgreSQL primary |
| Alerts | 1 year | PostgreSQL primary |
| Processing metrics/logs | 90 days | Axiom / log storage |

### 5.4 Continuous Contract Handling

The system handles continuous futures contracts through the following process:

1. **Contract Calendar Maintenance.** Store each instrument's valid contract months and compute expiration dates using exchange rules. Update the `instruments.current_contract` field when approaching roll dates.

2. **Roll Detection.** Monitor volume crossover between current and next-month contracts. Trigger roll when: (a) the next-month contract's volume exceeds the current month's for 2 consecutive sessions, OR (b) the configurable days-before-first-notice-day threshold is reached (default: 3 trading days).

3. **Price Adjustment.** On roll day, compute the settlement price gap between old and new contract. Apply an additive back-adjustment to all historical prices: `adjusted_price = raw_price + cumulative_adjustment`. This preserves the shape of trendlines across contract boundaries.

4. **Trendline Recalculation.** After price adjustment, trigger a full trendline recalculation for the instrument. Existing trendline anchor and touch prices are updated to the adjusted series. Grades and scores are recomputed.

5. **Symbol Mapping.** Maintain a real-time mapping table from generic symbols to broker-specific contract identifiers for order routing.

---

## 6. Dependencies on Other PRDs

| PRD | Dependency | Type | Description |
|---|---|---|---|
| PRD-001: Platform Foundation & Infrastructure | Hard | Database schema, authentication, user management, API framework (FastAPI), Celery/Redis task queue, deployment infrastructure. The detection engine requires these foundational services to operate. |
| PRD-003: Trade Execution Pipeline | Soft | The detection engine generates signals that feed into the execution pipeline. Break alerts include bracket order specifications that the execution pipeline consumes. The engine can operate independently (alert-only mode) without the execution pipeline. |
| PRD-004: Trade Journaling | Soft | Trendline metadata (grade, touch count, slope, etc.) is attached to journal entries when a trade is executed on a detected trendline. The engine can operate without journaling. |
| PRD-005: Playbook System | Soft | Auto-classification of trades into playbooks (A+ Trendline Break, Standard Break, Bounce) depends on trendline grade data from the detection engine. |
| PRD-006: Performance Analytics | Soft | Trendline-specific analytics (win rate by touch count, edge by slope angle) depend on trendline metadata from the detection engine. |
| PRD-007: Notification System | Hard | Alert routing (Telegram, email, Discord, WebSocket) depends on the notification infrastructure. The detection engine generates alert payloads; PRD-007 handles delivery. |
| PRD-008: Dashboard & Visualization | Soft | Chart overlay rendering of detected trendlines depends on the frontend charting component (TradingView Lightweight Charts). The engine provides line coordinates; the dashboard renders them. |
| PRD-009: AI/ML Features | Soft | False breakout filtering and trendline quality prediction ML models consume detection engine output as features. These are Phase 2+ enhancements. |
| PRD-010: Market Data Service | Hard | The detection engine depends on reliable 4H OHLCV data delivery. PRD-010 defines the data ingestion, normalization, and gap-fill infrastructure that feeds candles to the detection engine. If PRD-010 is not separately scoped, data ingestion requirements (TD-FR-001 through TD-FR-008) are owned by this PRD. |
| PRD-011: Broker Adapters | Soft | Continuous contract symbol mapping and real-time data feeds depend on broker adapter implementations. |

### Dependency Graph (Simplified)

```
PRD-001 (Foundation) ──> PRD-002 (Trendline Engine) ──> PRD-003 (Execution)
PRD-010 (Market Data) ──> PRD-002 (Trendline Engine) ──> PRD-007 (Notifications)
                                                    ──> PRD-008 (Dashboard)
                                                    ──> PRD-004 (Journaling)
                                                    ──> PRD-005 (Playbooks)
                                                    ──> PRD-006 (Analytics)
                                                    ──> PRD-009 (AI/ML)
```

---

## 7. Testing Requirements

### 7.1 Backtesting Against Historical Known Setups

| ID | Requirement | Priority |
|---|---|---|
| TD-TEST-001 | Create a reference dataset of >=50 manually identified A+ trendline setups across Phase 1 instruments, covering at least 12 months of historical data. Each entry SHALL include: instrument, direction, anchor points, touch points, slope, grade assessment, and outcome (profitable break / false break / no break). | P0 |
| TD-TEST-002 | Run the detection engine against the same 12-month historical data and measure detection rate: (engine-detected setups that overlap with manual reference) / (total manual reference setups). Target: >=80%. | P0 |
| TD-TEST-003 | Measure false positive rate: (engine-detected A+ lines NOT in manual reference) / (total engine-detected A+ lines). Target: <=20%. | P0 |
| TD-TEST-004 | Document and analyze every false negative (manual setup missed by engine) to identify systematic gaps in the algorithm. Categorize by failure mode: insufficient pivot detection, overly strict spacing, slope miscalculation, etc. | P0 |
| TD-TEST-005 | Create automated regression test suite that runs the engine against the reference dataset on every code change, alerting on accuracy degradation >2 percentage points. | P1 |

### 7.2 Visual Verification Tooling

| ID | Requirement | Priority |
|---|---|---|
| TD-TEST-010 | Build a visual verification tool (standalone Python script or Jupyter notebook) that renders: (a) the instrument's candlestick chart, (b) all detected pivot points (marked), (c) all qualifying trendlines (drawn), (d) touch points (highlighted), (e) grade and score annotations. | P0 |
| TD-TEST-011 | The visual tool SHALL support side-by-side comparison of engine-detected trendlines versus manually drawn reference lines. | P1 |
| TD-TEST-012 | The visual tool SHALL allow the reviewer to flag each detected trendline as "correct", "incorrect", or "debatable" and export the review results for accuracy measurement. | P1 |
| TD-TEST-013 | The visual tool SHALL support rendering with different parameter configurations to visually demonstrate the effect of parameter changes on detection results. | P2 |

### 7.3 Statistical Accuracy Measurement

| ID | Requirement | Priority |
|---|---|---|
| TD-TEST-020 | Compute precision, recall, and F1 score for trendline detection against the manual reference dataset. Report separately for each grade (A+, A, B). | P0 |
| TD-TEST-021 | Compute touch count accuracy: for each correctly detected trendline, compare the engine's touch count to the manual expert's touch count. Target: within +/-1 touch for >=90% of lines. | P0 |
| TD-TEST-022 | Compute slope measurement accuracy: for each correctly detected trendline, compare the engine's slope measurement to the manual expert's slope. Target: within +/-5 degrees for >=90% of lines. | P1 |
| TD-TEST-023 | Compute grade agreement rate: for each correctly detected trendline, compare the engine's grade assignment to the manual expert's grade. Target: exact match for >=85% of lines. | P1 |
| TD-TEST-024 | Track accuracy metrics over time (weekly/monthly) to detect algorithmic drift or degradation as the codebase evolves. | P2 |

### 7.4 Performance Benchmarking

| ID | Requirement | Priority |
|---|---|---|
| TD-TEST-030 | Benchmark full pipeline execution time (ingest candle -> detect pivots -> generate candidates -> score -> filter -> rank -> evaluate alerts) for a single instrument with 6 months of 4H data (~600 candles). Target: <10 seconds. | P0 |
| TD-TEST-031 | Benchmark incremental pipeline execution time (single new candle -> incremental pivot check -> update existing lines -> evaluate alerts) for a single instrument. Target: <5 seconds. | P0 |
| TD-TEST-032 | Benchmark parallel pipeline execution for 6 instruments simultaneously on a single Celery worker. Target: <30 seconds total. | P0 |
| TD-TEST-033 | Benchmark memory usage during pipeline execution. Target: <512 MB per instrument, <2 GB total for 6 instruments. | P1 |
| TD-TEST-034 | Benchmark database query performance for trendline retrieval: fetch all active trendlines for an instrument. Target: <100ms. | P1 |
| TD-TEST-035 | Load test: simulate 100 concurrent users each watching 10 instruments (1,000 instrument-user pairs) and verify alert delivery latency remains <30 seconds (p95). | P2 |

### 7.5 Unit and Integration Tests

| ID | Requirement | Priority |
|---|---|---|
| TD-TEST-040 | Unit tests for pivot detection: verify N-bar confirmation logic with known input sequences. Cover edge cases: flat highs/lows, gaps, single-candle spikes. | P0 |
| TD-TEST-041 | Unit tests for candidate line generation: verify pairwise line construction, slope calculation, and forward projection. | P0 |
| TD-TEST-042 | Unit tests for touch scoring: verify ATR-scaled tolerance, wick-only intersection logic, spacing quality calculation. | P0 |
| TD-TEST-043 | Unit tests for grading: verify A+/A/B grade assignment against known trendline parameters. | P0 |
| TD-TEST-044 | Unit tests for ranking: verify composite score formula and sort order. | P0 |
| TD-TEST-045 | Unit tests for break detection: verify close-past-line logic for both support and resistance, including edge cases (close exactly on line, wick past but body not). | P0 |
| TD-TEST-046 | Integration tests: end-to-end pipeline from candle ingestion to alert generation, using fixture data with known expected outputs. | P0 |
| TD-TEST-047 | Integration tests: trendline lifecycle state transitions (detected -> qualifying -> active -> traded -> invalidated). | P0 |
| TD-TEST-048 | Integration tests: contract rollover handling with price adjustment and trendline recalculation. | P1 |

---

## 8. Security Considerations

### 8.1 Data Security

| ID | Requirement | Priority |
|---|---|---|
| TD-SEC-001 | All OHLCV market data SHALL be treated as non-sensitive (publicly available data). No encryption-at-rest requirements beyond database-level encryption provided by Supabase/PostgreSQL. | P0 |
| TD-SEC-002 | User detection configurations SHALL be isolated by `user_id` with PostgreSQL Row-Level Security (RLS) policies. A user SHALL NOT be able to read, modify, or delete another user's configuration, trendlines, or alerts. | P0 |
| TD-SEC-003 | Trendline data SHALL be scoped to individual users. Even if two users are watching the same instrument with the same parameters, their trendline records are independent (no shared state). | P0 |
| TD-SEC-004 | Alert payloads transmitted via Telegram, Discord, or email SHALL NOT contain account balances, position sizes, or broker credentials. Alert content is limited to instrument, direction, prices, and trendline metadata. | P0 |

### 8.2 API Security

| ID | Requirement | Priority |
|---|---|---|
| TD-SEC-010 | All detection engine API endpoints SHALL require authentication (JWT or API key). Unauthenticated requests SHALL receive 401 responses. | P0 |
| TD-SEC-011 | Rate limiting SHALL be applied to configuration change endpoints (max 10 changes per minute per user) to prevent abuse of the recalculation trigger. | P0 |
| TD-SEC-012 | Webhook endpoints for receiving market data from external sources SHALL validate request signatures (HMAC-SHA256) to prevent injection of false data. | P1 |

### 8.3 Broker API Credential Security

| ID | Requirement | Priority |
|---|---|---|
| TD-SEC-020 | Broker API credentials used for market data ingestion SHALL be stored encrypted (AES-256) in the database or in a secrets manager (e.g., Railway secrets, AWS Secrets Manager). They SHALL NOT appear in logs, configuration files, or error messages. | P0 |
| TD-SEC-021 | Broker API connections SHALL use TLS 1.2+ for all communications. | P0 |
| TD-SEC-022 | Broker API tokens that expire (Tradovate OAuth: hourly, Webull app secret: 24h-7d) SHALL be refreshed automatically without manual intervention. Token refresh failures SHALL trigger monitoring alerts. | P0 |

### 8.4 Operational Security

| ID | Requirement | Priority |
|---|---|---|
| TD-SEC-030 | Processing logs SHALL NOT contain raw OHLCV data (which could be valuable for competitors if the system scales to proprietary data sources). Logs SHALL contain only metadata: instrument, candle count, processing time, alert count. | P1 |
| TD-SEC-031 | The detection engine SHALL NOT have write access to the trade execution database tables. It produces alerts; the execution pipeline consumes them. Separation of concerns prevents a detection engine bug from placing orders. | P0 |
| TD-SEC-032 | Celery workers processing trendline detection SHALL run with minimal database permissions: SELECT on candles/instruments, INSERT/UPDATE on trendlines/pivots/alerts/trendline_events, no DELETE, no DDL. | P1 |

---

## 9. Phase Mapping

### Phase 1: Personal Trading System (Weeks 3-4)

**Goal:** Working detection engine for 3-6 instruments (Platinum, Crude Oil, Gold as primary; YM, MES, MNQ as secondary). Alert-only mode (no auto-execution). Single user.

| Deliverable | Requirements Covered | Details |
|---|---|---|
| Historical data bootstrapping | TD-FR-001, TD-FR-003, TD-FR-006, TD-FR-007 | Fetch 6+ months of daily data via yfinance, backfill 4H data from IBKR. Store in PostgreSQL. |
| Incremental 4H candle ingestion | TD-FR-002, TD-FR-004, TD-FR-005, TD-FR-008 | Celery beat task every 4 hours during market hours. IBKR primary, Tradovate fallback. |
| Swing point detection | TD-FR-010, TD-FR-011, TD-FR-013, TD-FR-014, TD-FR-016 | scipy.signal.find_peaks with N=5 default. Store pivots in database. |
| Candidate line generation | TD-FR-020, TD-FR-021, TD-FR-023, TD-FR-024, TD-FR-025, TD-FR-026 | Exhaustive pairwise search. Body-cross rejection. Forward projection. |
| Touch scoring | TD-FR-030, TD-FR-031, TD-FR-033, TD-FR-034, TD-FR-035, TD-FR-036 | 0.5x ATR tolerance, wick-only, spacing enforcement. |
| Quality grading (A+/A/B) | TD-FR-040, TD-FR-041, TD-FR-044 | Full grading rubric. Broken-line rejection. |
| Ranking and surfacing | TD-FR-050, TD-FR-051, TD-FR-052, TD-FR-053, TD-FR-054, TD-FR-056 | Composite score formula. Top 5 per instrument per direction. |
| Break and touch alerts | TD-FR-060, TD-FR-061, TD-FR-064, TD-FR-065, TD-FR-066, TD-FR-067, TD-FR-069 | Telegram + WebSocket delivery. Deduplication. Bracket order spec in payload. |
| Basic lifecycle management | TD-FR-070, TD-FR-071, TD-FR-072, TD-FR-073, TD-FR-074, TD-FR-075 | State machine: detected -> qualifying -> active -> traded / invalidated. |
| Default configuration | TD-FR-080, TD-FR-081 | Tori Trades A+ defaults. Single user, no multi-tenant. |
| Phase 1 instruments | TD-FR-090, TD-FR-094 | PL, CL, GC, YM, MES, MNQ. |
| Basic contract mapping | TD-FR-100, TD-FR-101, TD-FR-103 | Manual roll date entry initially. Static symbol mapping. |
| Visual verification notebook | TD-TEST-010 | Jupyter notebook for visual QA of detected trendlines. |
| Core unit tests | TD-TEST-040 through TD-TEST-046 | Full unit test suite for all pipeline stages. |
| Reference dataset (initial) | TD-TEST-001 | 20+ manually identified setups for initial validation. |

**Phase 1 Instrument Limit:** 3-10 instruments.
**Phase 1 User Limit:** 1 (personal use).
**Phase 1 Configuration:** Hardcoded defaults, minimal UI for parameter changes.

### Phase 2: Multi-Tenant & Expanded Coverage (Weeks 9-14)

**Goal:** Multi-user support with per-user configuration. Expanded to 50 instruments. A/B grade alerts. ML-assisted quality scoring.

| Deliverable | Requirements Covered | Details |
|---|---|---|
| Williams Fractals alternative | TD-FR-012 | N=2 high-sensitivity mode as user-selectable option. |
| RANSAC optimization | TD-FR-022 | For instruments with >50 pivots, switch to RANSAC for performance. |
| Historical ATR for touch scoring | TD-FR-032 | Use ATR at touch time, not current ATR. |
| Incremental pivot evaluation | TD-FR-015 | Avoid full recalculation on every candle. |
| New A+ and Invalidation alerts | TD-FR-062, TD-FR-063, TD-FR-068 | Grade promotion alerts. Invalidation alerts. Quiet hours. |
| Full lifecycle management | TD-FR-076, TD-FR-077, TD-FR-078 | Expiration state. Event history. Manual dismissal. |
| Per-user configuration | TD-FR-082, TD-FR-083, TD-FR-084 | Validation, recalculation trigger, reset to defaults. |
| Instrument watchlist management | TD-FR-091, TD-FR-092, TD-FR-093 | Add/remove with tier limits. Background data fetch on add. |
| Automated contract rollover | TD-FR-102, TD-FR-104, TD-FR-105 | Volume-based roll detection. Price adjustment. Full recalculation. |
| User configuration recompute | TD-FR-045 | Grade recalculation on config change. |
| Proximity-based deprioritization | TD-FR-055 | Deprioritize lines far from current price. |
| Expanded reference dataset | TD-TEST-001 (expanded) | 50+ setups across all Phase 2 instruments. |
| Automated regression suite | TD-TEST-005 | CI/CD accuracy regression test. |
| Side-by-side comparison tool | TD-TEST-011, TD-TEST-012 | Visual verification with flagging workflow. |
| Statistical accuracy reporting | TD-TEST-020, TD-TEST-021, TD-TEST-022, TD-TEST-023 | Precision/recall/F1 dashboard. |
| Email and Discord alert routing | TD-FR-065 (expanded) | Additional notification channels. |
| Configuration presets | TD-FR-085 | Named presets (Tori A+ Strict, High Sensitivity, Conservative). |

**Phase 2 Instrument Limit:** Up to 50 instruments (expanded CME, ICE, CBOT coverage).
**Phase 2 User Limit:** Up to 100 concurrent users.
**Phase 2 Configuration:** Full UI for all parameters. Preset system.

### Phase 3: Scale & Advanced Features (Months 6-12)

**Goal:** Unlimited instruments. 1,000+ users. ML-powered false breakout filtering. Strategy-aware detection.

| Deliverable | Requirements Covered | Details |
|---|---|---|
| Unlimited instrument support | TD-NFR-022 | 200+ instruments. Dynamic worker scaling. |
| 1,000+ user scalability | TD-NFR-023 | Shared computation for same-instrument/same-config users. |
| Load testing | TD-TEST-035 | 100 users x 10 instruments stress test. |
| Accuracy tracking over time | TD-TEST-024 | Weekly accuracy dashboard with drift detection. |
| Multi-parameter visual comparison | TD-TEST-013 | Compare detection results across parameter sets. |
| Contract rollover automation | TD-FR-102 (enhanced) | Fully automated roll with zero manual intervention. |
| Push notification alerts | TD-FR-065 (P2 channels) | Mobile push notifications. |
| ML quality scoring | (PRD-009 dependency) | Gradient-boosted classifier for break probability. |
| Multi-timeframe detection | Future scope | Extend beyond 4H to 1H, daily, weekly. |

**Phase 3 Instrument Limit:** Unlimited.
**Phase 3 User Limit:** 1,000+.
**Phase 3 Configuration:** API-driven configuration for programmatic access.

---

## 10. Acceptance Criteria

### 10.1 Phase 1 Launch Criteria (All must pass)

| # | Criterion | Measurement Method | Pass Threshold |
|---|---|---|---|
| AC-001 | Detection accuracy against manual reference dataset | Run engine on 12-month historical data, compare to 20+ manually identified A+ setups | >=80% of manual setups detected (recall) |
| AC-002 | False positive rate | Expert review of all engine-surfaced A+ trendlines on historical data | <=20% of surfaced lines rejected by expert |
| AC-003 | End-to-end latency | Measure time from 4H candle data availability to Telegram alert delivery, over 20 consecutive candle cycles | p95 <30 seconds |
| AC-004 | Zero missed candle ingestion | Monitor candle ingestion log over 30 consecutive trading days | 0 gaps in 4H candle data |
| AC-005 | Break detection determinism | Test with 50 known break scenarios (candle close past line) | 100% correctly identified |
| AC-006 | Touch detection accuracy | Compare engine touch counts to manual counts on 30 trendlines | >=90% within +/-1 touch of manual count |
| AC-007 | Lifecycle state integrity | Execute full lifecycle test (detected -> qualifying -> active -> traded) on 10 trendlines | All 10 transition correctly |
| AC-008 | Alert deduplication | Trigger the same break event 3 times in sequence | Exactly 1 alert delivered |
| AC-009 | Pipeline stability | Run engine continuously for 7 days (including weekend market close/open transition) | Zero unhandled exceptions, zero worker crashes |
| AC-010 | Configuration parameter validation | Attempt to set each parameter to out-of-range values | All out-of-range values rejected with descriptive errors |
| AC-011 | Bracket order specification in break alerts | Verify 10 break alerts contain valid entry, stop, and target prices | All 10 have correct bracket specs with >=2R target |
| AC-012 | Contract symbol mapping | Verify symbol mapping for all 6 Phase 1 instruments | All 6 map correctly to IBKR and Tradovate symbols |
| AC-013 | Visual verification | Expert reviews 10 detected trendlines on candlestick charts using the verification notebook | >=8 of 10 judged "correct" or "acceptable" |

### 10.2 Ongoing Operational Criteria

| Criterion | Measurement | Frequency | Threshold |
|---|---|---|---|
| Detection accuracy (regression) | Automated test suite against reference dataset | Every deployment | No degradation >2 percentage points from baseline |
| Alert delivery success rate | Monitor delivery confirmations across all channels | Daily | >=99.9% |
| Pipeline processing time | Track p50/p95/p99 per-instrument processing time | Every run | p95 <10 seconds per instrument |
| Data freshness | Monitor gap between latest candle timestamp and current time | Continuous | Gap <5 minutes during market hours |
| System uptime during market hours | Uptime monitoring (Uptime Robot or equivalent) | Continuous | >=99.5% monthly |

### 10.3 Quality Gate: Manual Trader Equivalence Test

The definitive acceptance test for the detection engine is the **Manual Trader Equivalence Test**:

1. Select 5 trading days (1 trading week) during which the engine is running in production.
2. An experienced trendline trader independently scans the same instruments using only TradingView (manual process).
3. At the end of each day, compare:
   - **Setups the engine found that the trader also found** (true positives)
   - **Setups the engine found that the trader did not find** (potential false positives, reviewed individually)
   - **Setups the trader found that the engine missed** (false negatives)
4. Calculate: `equivalence_score = true_positives / (true_positives + false_negatives)`
5. **Pass criterion:** equivalence_score >= 0.80 across the 5-day test period.

This test SHALL be repeated quarterly to ensure ongoing accuracy as the codebase evolves and market conditions change.

---

## Appendix A: Algorithm Pseudocode

### A.1 Detection Pipeline (Per Instrument)

```
function detect_trendlines(instrument, config):
    # 1. Load data
    candles = fetch_4h_candles(instrument, lookback=6_months)
    atr = compute_atr(candles, period=14)

    # 2. Detect pivots
    pivot_highs = find_peaks(candles.high, distance=config.n_bar_lookback)
    pivot_lows = find_peaks(-candles.low, distance=config.n_bar_lookback)

    # 3. Generate candidates (support lines from lows, resistance from highs)
    candidates = []
    for pivot_set in [pivot_lows, pivot_highs]:
        direction = SUPPORT if pivot_set == pivot_lows else RESISTANCE
        for i in range(len(pivot_set)):
            for j in range(i+1, len(pivot_set)):
                line = construct_line(pivot_set[i], pivot_set[j])
                if not body_crosses_line(candles, line):
                    candidates.append((line, direction))

    # 4. Score each candidate
    scored = []
    for (line, direction) in candidates:
        touches = find_touches(candles, line, direction, atr, config.touch_tolerance)
        touches = enforce_spacing(touches, config.min_candle_spacing)
        touch_count = len(touches) + 2  # +2 for anchor points

        if touch_count < config.min_touch_count:
            continue

        slope_deg = compute_slope_degrees(line)
        if slope_deg > config.max_slope_degrees:
            continue

        duration_days = (touches[-1].timestamp - touches[0].timestamp).days
        if duration_days < config.min_duration_days:
            continue

        spacing_quality = compute_spacing_quality(touches)
        duration_factor = log2(duration_days / 7 + 1)
        inverse_slope = 1 - (slope_deg / 90)
        score = touch_count * spacing_quality * duration_factor * inverse_slope

        grade = assign_grade(touch_count, min_spacing, slope_deg, duration_days)
        scored.append(Trendline(line, direction, touches, score, grade))

    # 5. Rank and surface top N
    scored.sort(key=lambda t: t.score, reverse=True)
    support_lines = [t for t in scored if t.direction == SUPPORT][:config.max_lines]
    resistance_lines = [t for t in scored if t.direction == RESISTANCE][:config.max_lines]

    return support_lines + resistance_lines
```

### A.2 Alert Evaluation (Per New 4H Candle)

```
function evaluate_alerts(instrument, new_candle, active_trendlines):
    alerts = []
    atr = get_current_atr(instrument)

    for trendline in active_trendlines:
        projected_price = trendline.project_to(new_candle.timestamp)

        if trendline.direction == SUPPORT:
            # Break: candle body closes below line
            if new_candle.close < projected_price:
                if trendline.status != TRADED:
                    alerts.append(BreakAlert(trendline, new_candle, SHORT))
                    trendline.status = INVALIDATED if not traded else TRADED
            # Touch: wick reaches within tolerance
            elif abs(new_candle.low - projected_price) <= config.touch_tolerance * atr:
                alerts.append(TouchAlert(trendline, new_candle))

        elif trendline.direction == RESISTANCE:
            # Break: candle body closes above line
            if new_candle.close > projected_price:
                if trendline.status != TRADED:
                    alerts.append(BreakAlert(trendline, new_candle, LONG))
                    trendline.status = INVALIDATED if not traded else TRADED
            # Touch: wick reaches within tolerance
            elif abs(new_candle.high - projected_price) <= config.touch_tolerance * atr:
                alerts.append(TouchAlert(trendline, new_candle))

    return alerts
```

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| **ATR** | Average True Range. A volatility measure computed as the 14-period exponential moving average of the true range (max of: high-low, abs(high-prev_close), abs(low-prev_close)). |
| **Back-adjustment** | A method of constructing continuous futures price series by adding a fixed offset to historical prices at each contract roll, preserving price differences (and thus trendline slopes). |
| **Bracket order** | A compound order consisting of an entry order, a stop-loss order, and a take-profit order. |
| **Continuous contract** | A synthetic price series constructed by stitching together individual futures contract data across roll dates, enabling technical analysis over periods longer than a single contract's life. |
| **First Notice Day** | The first day on which a buyer of a futures contract may be required to take delivery. Most speculative traders roll positions before this date. |
| **N-bar confirmation** | A pivot point is confirmed when N candles on each side have lower highs (for pivot high) or higher lows (for pivot low). Higher N = fewer, more significant pivots. |
| **Pivot point** | A swing high or swing low identified by N-bar confirmation. Pivots are the anchor points and touch points for trendlines. |
| **RANSAC** | Random Sample Consensus. An iterative algorithm for robust model fitting in the presence of outliers. Used when the number of pivot points is large enough that exhaustive search is computationally expensive. |
| **R-multiple** | The profit or loss of a trade expressed as a multiple of the initial risk (distance from entry to stop loss). A 2R trade earned twice its initial risk. |
| **Safety line** | The opposing trendline projected 4 candles forward from the break point. Used as the stop-loss level in the Tori Trades methodology. |
| **S/R level** | Support or Resistance. A horizontal price level where price has historically reversed or consolidated. Used to set take-profit targets. |
| **Touch** | A candle whose wick (not body) intersects a trendline within the ATR-scaled tolerance. A key quality metric for trendlines. |
| **Williams Fractals** | A specific case of N-bar confirmation with N=2, producing more frequent (noisier) pivot point detection. Named after Bill Williams. |

---

## Appendix C: Reference Documents

- [TrendEdge Master PRD v1.0](/Users/arieldigital/Apps/trendedge/_docs/TrendEdge%20PRD%20v1.md)
- Tori Trades Playbook: [tradezella.com/playbooks/trendline-strategy](https://tradezella.com/playbooks/trendline-strategy)
- pytrendline Library: [github.com/ednunezg/pytrendline](https://github.com/ednunezg/pytrendline)
- trendln Library: [github.com/GregoryMorse/trendln](https://github.com/GregoryMorse/trendln)
- scipy.signal.find_peaks: [docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html)
- RANSAC (scikit-learn): [scikit-learn.org/stable/modules/generated/sklearn.linear_model.RANSACRegressor.html](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.RANSACRegressor.html)
