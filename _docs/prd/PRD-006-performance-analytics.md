# PRD-006: Performance Analytics Dashboard

**Product:** TrendEdge — AI-Powered Futures Trading Platform
**Feature:** Performance Analytics Dashboard
**Version:** 1.0
**Date:** February 11, 2026
**Status:** Draft
**Author:** Product Team
**Dependencies:** PRD-003 (Trade Execution Pipeline), PRD-004 (Trade Journaling), PRD-005 (Playbook System)

---

## Table of Contents

1. [Overview and Purpose](#1-overview-and-purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Dependencies](#5-dependencies)
6. [Testing Requirements](#6-testing-requirements)
7. [Security Requirements](#7-security-requirements)
8. [Phase Mapping](#8-phase-mapping)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. Overview and Purpose

### 1.1 Problem Statement

Retail futures traders lack a unified analytics system that connects trade execution data, journal context, playbook classification, and trendline quality metadata into a single performance dashboard. Today, traders export CSVs from their broker, paste data into spreadsheets, and manually compute metrics that should be automatic. Critical analytics like R-multiple distributions, MAE/MFE scatter plots, and trendline-specific performance breakdowns are effectively impossible to produce without custom tooling.

The traders who do use journaling tools (TradeZella, Edgewonk, Tradervue) face a fundamental data gap: their analytics cannot incorporate trendline detection metadata (touch count, slope angle, duration) because that data does not exist in their systems. TrendEdge closes this loop by generating analytics from the same system that detected the setup, executed the trade, and journaled the result.

### 1.2 Purpose

The Performance Analytics Dashboard is TrendEdge's data layer for continuous trader improvement. It transforms raw trade execution records, journal entries, and playbook tags into actionable metrics, visualizations, and AI-powered insights. The dashboard answers the questions that matter to a systematic futures trader:

- "Is my edge real, or am I just lucky?" (Monte Carlo simulation, expectancy, profit factor)
- "Which setups should I stop trading?" (playbook-level performance breakdown)
- "Am I executing well or leaving money on the table?" (MAE/MFE analysis, slippage tracking)
- "When am I at my worst?" (time-of-day analysis, behavioral metrics, Tiltmeter)
- "Are my trendline criteria actually predictive?" (win rate by touch count, slope, duration)

### 1.3 Scope

This PRD covers the complete Performance Analytics Dashboard including:

- Core metrics calculation engine (7 metric categories, 30+ individual metrics)
- Dashboard layout, widget system, and interactive filtering
- Chart visualizations (equity curve, P&L calendar, R-multiple histogram, MAE/MFE scatter, drawdown chart, time analysis)
- Advanced analytics for Pro tier (Monte Carlo simulation, strategy correlation, walk-forward analysis, AI insights)
- Comparative analytics (paper vs. live, period vs. period, strategy A vs. B)
- Dashboard export to PDF
- Real-time updates via WebSocket
- Team-level analytics for Team tier

### 1.4 Architecture Overview

| Layer | Technology | Role |
|---|---|---|
| Frontend | Next.js 14+ (App Router) + TypeScript + Tailwind + shadcn/ui | Dashboard shell, layout, filters, responsive design |
| Charting | Recharts (standard charts) + D3.js (custom visualizations) | Equity curves, histograms, scatter plots, heatmaps, calendar |
| Backend API | FastAPI (Python 3.12+) | Metrics computation endpoints, WebSocket server, export generation |
| Database | PostgreSQL 16 (Supabase) | Trade data storage, materialized views for aggregations, RLS |
| Cache | Redis (Upstash) | Computed metrics cache, WebSocket pub/sub |
| PDF Export | WeasyPrint or Playwright PDF | Server-side PDF report generation |
| Hosting | Vercel (frontend) + Railway (backend) | Production deployment |

---

## 2. User Stories

### 2.1 Core Dashboard Usage

**US-AN-001: Daily Performance Review**
As a futures trader, I want to open my analytics dashboard after the trading session and immediately see today's P&L, win rate, and cumulative equity curve so that I can assess my daily performance in under 10 seconds.

**US-AN-002: Playbook Performance Comparison**
As a trader using multiple setups, I want to filter my analytics by playbook (A+ Trendline Break, Standard Break, Bounce) so that I can identify which setups have a genuine statistical edge and which I should stop trading.

**US-AN-003: Instrument-Level Analysis**
As a trader who trades Crude Oil (CL), Gold (GC), Platinum (PL), and Dow (YM), I want to filter all metrics by instrument so that I can determine which markets I trade best and allocate my attention accordingly.

**US-AN-004: Time Period Analysis**
As a trader, I want to switch between preset date ranges (7 days, 30 days, 90 days, YTD, all-time) and custom date ranges so that I can analyze performance across different market conditions and personal development phases.

### 2.2 Execution Quality

**US-AN-005: Slippage Tracking**
As a trader concerned about execution quality, I want to see my average slippage per instrument and per broker so that I can identify whether my fill quality is costing me money and whether I should switch order types or brokers.

**US-AN-006: MAE/MFE Analysis**
As a trader optimizing my stop and target placement, I want to see scatter plots of Maximum Adverse Excursion and Maximum Favorable Excursion for all trades so that I can determine whether my stops are too tight (getting stopped out before trades work) or my targets too conservative (leaving profit on the table).

### 2.3 Risk and Drawdown

**US-AN-007: Drawdown Monitoring**
As a trader managing risk, I want to see my underwater equity curve (drawdown chart) with peak-to-trough measurements, recovery time, and drawdown clustering so that I can understand my risk profile and set appropriate daily loss limits.

**US-AN-008: Risk-Adjusted Metrics**
As a trader evaluating my strategy holistically, I want to see Sharpe ratio, Sortino ratio, and Calmar ratio calculated on my actual trading results so that I can compare my risk-adjusted returns against benchmarks and across time periods.

### 2.4 Behavioral Analytics

**US-AN-009: Rule Compliance Tracking**
As a trader working on discipline, I want to see my rule compliance rate (percentage of trades where I followed my playbook rules) alongside the dollar cost of rule violations so that I can quantify the financial impact of my mistakes.

**US-AN-010: Tiltmeter Score**
As a trader prone to emotional trading, I want a composite behavioral score (Tiltmeter) that aggregates my emotional state tags, mistake frequency, and deviation from planned risk so that I get an early warning when I am trading on tilt.

### 2.5 Trendline-Specific Analytics

**US-AN-011: Trendline Quality Correlation**
As a trendline trader, I want to see my win rate and average R-multiple broken down by trendline touch count, slope angle, and duration so that I can validate whether the A+ criteria (3+ touches, <45 degrees, 3+ weeks) genuinely predict better outcomes in my own trading.

### 2.6 Advanced Analytics (Pro Tier)

**US-AN-012: Monte Carlo Projection**
As a Pro tier trader, I want to run Monte Carlo simulations on my trade history to see projected equity curves with 5th, 25th, 50th, 75th, and 95th percentile confidence intervals so that I can understand the range of possible outcomes and set realistic expectations.

**US-AN-013: Strategy Decay Detection**
As a Pro tier trader, I want walk-forward analysis showing rolling performance windows (30-trade, 60-trade, 90-trade) so that I can detect when a strategy is decaying and needs adjustment before significant capital loss.

**US-AN-014: AI-Powered Insights**
As a Pro tier trader, I want to ask natural language questions about my trading data ("What is my best setup on Tuesdays in crude oil?", "Show me all losing trades where I moved my stop") and receive accurate, data-backed answers so that I can explore my performance without building custom queries.

**US-AN-015: Comparative Analytics**
As a trader transitioning from paper to live, I want to compare my paper trading equity curve side-by-side with my live trading curve, and compare any two time periods, so that I can identify performance differences caused by psychological factors vs. market conditions.

### 2.7 Export and Reporting

**US-AN-016: PDF Report Generation**
As a trader, I want to export my analytics dashboard as a formatted PDF report with my selected date range, filters, and all visible charts so that I can share my performance with mentors, prop firm evaluators, or keep personal records.

### 2.8 Team Analytics (Team Tier)

**US-AN-017: Team Performance Overview**
As a team lead or prop firm manager on the Team tier, I want to see aggregated performance metrics across all team members with the ability to drill down into individual trader dashboards so that I can identify who needs coaching and which team-wide patterns exist.

---

## 3. Functional Requirements

### 3.1 Core Metrics Calculation Engine

#### AN-FR-001: Trade Performance Metrics

The system SHALL calculate the following trade performance metrics from the user's trade history:

| Metric | Formula | Precision |
|---|---|---|
| Win Rate | (winning trades / total trades) x 100 | 1 decimal (e.g., 62.5%) |
| Average Winner | sum(winning P&L) / count(winning trades) | 2 decimals, currency |
| Average Loser | sum(losing P&L) / count(losing trades) | 2 decimals, currency |
| Profit Factor | gross profit / gross loss | 2 decimals |
| Expectancy | (win rate x avg winner) - (loss rate x avg loser) | 2 decimals, currency |
| Largest Win | max(P&L where P&L > 0) | 2 decimals, currency |
| Largest Loss | min(P&L where P&L < 0) | 2 decimals, currency |
| Total Net P&L | sum(all P&L) | 2 decimals, currency |
| Total Trades | count(closed trades) | Integer |
| Average Trade Duration | avg(exit_time - entry_time) | Hours and minutes |

- Breakeven trades (P&L = 0 after commissions) SHALL be classified as losses for win rate calculation.
- All P&L calculations SHALL include commissions and fees.
- Metrics SHALL recalculate when filters change (date range, instrument, playbook).

#### AN-FR-002: Risk-Adjusted Metrics

The system SHALL calculate the following risk-adjusted performance metrics:

| Metric | Formula | Notes |
|---|---|---|
| Sharpe Ratio | (mean daily return - risk-free rate) / std(daily returns) | Annualized. Risk-free rate configurable, default 5.0% |
| Sortino Ratio | (mean daily return - risk-free rate) / std(negative daily returns) | Uses downside deviation only |
| Calmar Ratio | annualized return / max drawdown | Rolling 36-month or available history |
| Max Drawdown ($) | largest peak-to-trough decline in equity | Dollar amount |
| Max Drawdown (%) | max drawdown / equity at peak | Percentage |
| Recovery Time | trading days from trough to new equity high | Days; "ongoing" if not recovered |
| Average Drawdown | mean of all drawdown periods | Dollar amount |
| Drawdown Count | number of distinct drawdown periods | Integer |

- Daily returns SHALL be calculated from closed trade P&L attributed to the trade's exit date.
- Days with no trades SHALL be excluded from return calculations (trading days only).
- Sharpe and Sortino ratios require a minimum of 20 trading days with trades; display "Insufficient data" otherwise.

#### AN-FR-003: R-Multiple Analysis

The system SHALL calculate R-multiple metrics from trade data:

| Metric | Formula | Notes |
|---|---|---|
| R-Multiple per trade | actual P&L / initial risk (distance to stop x contract value) | 2 decimal precision |
| Average R | mean(all R-multiples) | 2 decimals |
| Median R | median(all R-multiples) | 2 decimals |
| R Expectancy | mean R-multiple (equivalent to system expectancy in R terms) | 2 decimals |
| Cumulative R | running sum of R-multiples over time | Chart data series |
| Best R | max(R-multiple) | 2 decimals |
| Worst R | min(R-multiple) | 2 decimals |

- R-multiple SHALL only be calculated for trades where initial risk (stop loss distance) is defined.
- Trades without a defined stop loss SHALL display "N/A" for R-multiple and be excluded from R-based aggregate metrics.

#### AN-FR-004: Time-Based Analysis Metrics

The system SHALL calculate P&L and win rate segmented by time dimensions:

| Dimension | Segments | Metrics per Segment |
|---|---|---|
| Hour of Day | 0-23 (exchange local time) | Net P&L, trade count, win rate |
| Day of Week | Monday through Friday | Net P&L, trade count, win rate, avg R |
| Month | January through December | Net P&L, trade count, win rate, avg R |
| Calendar Month (specific) | e.g., Jan 2026, Feb 2026 | Net P&L, trade count, win rate, avg R |
| Session | RTH (Regular Trading Hours), Overnight (Globex) | Net P&L, trade count, win rate, avg R |

- RTH session times SHALL be configurable per instrument. Defaults: ES/NQ/YM: 09:30-16:00 ET; CL: 09:00-14:30 ET; GC: 08:20-13:30 ET.
- A trade's session classification SHALL be based on the entry time.
- Hour-of-day analysis SHALL use the exchange's local timezone.

#### AN-FR-005: Execution Quality Metrics

The system SHALL calculate execution quality metrics:

| Metric | Formula | Notes |
|---|---|---|
| Average Slippage | mean(fill price - signal price) per side | In ticks and dollars |
| Slippage by Instrument | average slippage grouped by instrument | In ticks |
| Slippage by Broker | average slippage grouped by broker connection | In ticks |
| Fill Rate | orders filled / orders submitted | Percentage |
| MAE (Maximum Adverse Excursion) | max unfavorable price movement during trade | In ticks and dollars |
| MFE (Maximum Favorable Excursion) | max favorable price movement during trade | In ticks and dollars |
| Fill Quality Score | composite: (1 - normalized_slippage) x fill_rate | 0-100 scale |
| Edge Ratio | avg MFE / avg MAE | 2 decimals |

- Slippage SHALL be signed: positive = unfavorable (buy filled above signal, sell filled below signal), negative = favorable.
- MAE/MFE require tick-by-tick or bar-by-bar price data during the trade's holding period (sourced from PRD-003 execution pipeline).
- If tick data is unavailable for a trade, MAE/MFE SHALL be estimated from the bar data at the trade's timeframe and flagged as "estimated."

#### AN-FR-006: Behavioral Metrics

The system SHALL calculate behavioral metrics from journal entries (PRD-004):

| Metric | Formula | Data Source |
|---|---|---|
| Rule Compliance Rate | trades following all playbook rules / total trades | Journal rule compliance checklist |
| Cost of Mistakes | sum(P&L of trades with mistake tags) | Journal mistake tags |
| Mistake Frequency | trades with mistakes / total trades | Journal mistake tags |
| Mistake Breakdown | count and P&L per mistake type (moved stop, entered early, oversized, held too long, exited too early) | Journal mistake tags |
| Tiltmeter Score | weighted composite of: emotional state distribution, mistake frequency, deviation from planned position size, trade frequency anomaly | Journal emotional tags, trade sizing data |
| Average Conviction | mean(conviction level 1-5) | Journal conviction field |
| Conviction vs. Outcome Correlation | Pearson correlation: conviction level vs. R-multiple | Journal conviction + trade R-multiple |

**Tiltmeter Score Calculation:**

The Tiltmeter score ranges from 0 (fully disciplined) to 100 (severe tilt). It is a rolling metric computed over the last 10 trades:

| Component | Weight | Scoring |
|---|---|---|
| Emotional State | 25% | 0 if confident/patient/disciplined; 50 if anxious; 100 if FOMO/revenge |
| Mistake Rate | 30% | (trades with mistakes / last 10 trades) x 100 |
| Position Size Deviation | 25% | abs(actual size - planned size) / planned size x 100, capped at 100 |
| Trade Frequency Anomaly | 20% | (current frequency / baseline frequency - 1) x 100, capped at 100 |

- Baseline trade frequency SHALL be calculated as the user's average trades per week over the trailing 30 days.
- Tiltmeter SHALL display a color-coded gauge: 0-25 green (disciplined), 26-50 yellow (caution), 51-75 orange (elevated risk), 76-100 red (tilt).

#### AN-FR-007: Trendline-Specific Analytics

The system SHALL calculate performance metrics segmented by trendline characteristics (data sourced from PRD-003 trendline metadata):

| Dimension | Segments | Metrics per Segment |
|---|---|---|
| Touch Count | 2, 3, 4, 5+ | Win rate, avg R, profit factor, trade count |
| Slope Angle | 0-15 degrees, 15-30 degrees, 30-45 degrees, 45+ degrees | Win rate, avg R, profit factor, trade count |
| Trendline Duration | <1 week, 1-3 weeks, 3-8 weeks, 8+ weeks | Win rate, avg R, profit factor, trade count |
| Trendline Grade | A+, A, B | Win rate, avg R, profit factor, trade count |
| Setup Type | Break vs. Bounce | Win rate, avg R, profit factor, trade count |
| Candle Spacing | <6, 6-10, 10-20, 20+ candles | Win rate, avg R, profit factor, trade count |

- Trendline analytics SHALL only include trades that have trendline metadata attached (auto-classified from trendline engine).
- Manual/custom playbook trades without trendline metadata SHALL be excluded from trendline-specific analytics and a count of excluded trades SHALL be displayed.

### 3.2 Dashboard Layout and Widget System

#### AN-FR-008: Dashboard Layout

The dashboard SHALL use a responsive grid layout with the following structure:

**Default Layout (Desktop, 1280px+):**

| Row | Widgets |
|---|---|
| Row 1 | Summary stat cards (6 cards across): Total Net P&L, Win Rate, Profit Factor, Average R, Max Drawdown, Tiltmeter Score |
| Row 2 | Equity Curve (full width) |
| Row 3 | P&L Calendar Heatmap (2/3 width) + R-Multiple Histogram (1/3 width) |
| Row 4 | Win Rate by Dimension (1/2 width) + Time Analysis (1/2 width) |
| Row 5 | MAE/MFE Scatter (1/2 width) + Drawdown Chart (1/2 width) |
| Row 6 | Execution Quality Table (1/3 width) + Behavioral Metrics (1/3 width) + Trendline Analytics (1/3 width) |

**Tablet Layout (768px-1279px):** Two-column grid. Widgets stack to fill available width. Summary cards wrap to 3x2.

**Mobile Layout (<768px):** Single-column stack. Summary cards display as horizontally scrollable carousel. Charts render at full viewport width with reduced height. Interactive elements (tooltips, drill-down) use tap instead of hover.

#### AN-FR-009: Widget System

Each dashboard widget SHALL support:

- **Expand/Collapse:** Click widget header to toggle between compact and expanded view.
- **Full-Screen Mode:** Button to expand any chart to full viewport with enhanced detail.
- **Loading State:** Skeleton loader displayed while data is being fetched or computed.
- **Empty State:** Descriptive message when no data matches current filters. Example: "No trades match the selected filters. Try adjusting the date range or removing instrument filters."
- **Error State:** Inline error message with retry button if computation fails.
- **Tooltip:** Hover (desktop) or tap (mobile) on any data point to see detail values.

#### AN-FR-010: Dashboard Customization (Trader Tier and Above)

Users on Trader tier and above SHALL be able to:

- Reorder widgets via drag-and-drop.
- Hide/show individual widgets.
- Save layout as a named preset (up to 5 presets on Trader, unlimited on Pro/Team).
- Reset to default layout.
- Layout preferences SHALL persist across sessions (stored in user settings in PostgreSQL).

### 3.3 Filtering System

#### AN-FR-011: Date Range Filtering

The dashboard SHALL support the following date range selections:

| Preset | Definition |
|---|---|
| Today | Current calendar date (exchange timezone) |
| 7 Days | Last 7 calendar days including today |
| 30 Days | Last 30 calendar days including today |
| 90 Days | Last 90 calendar days including today |
| YTD | January 1 of current year through today |
| All Time | First trade date through today |
| Custom | User-selected start and end date via date picker |

- The date picker SHALL use a calendar UI component with click-to-select start and click-to-select end.
- The selected date range SHALL be displayed prominently in the dashboard header.
- Changing the date range SHALL trigger a recalculation of all visible metrics and charts.
- The default date range on first load SHALL be "30 Days."
- Date range selection SHALL persist in the URL query parameters (e.g., `?range=30d` or `?start=2026-01-01&end=2026-01-31`) to support bookmarking and sharing.

#### AN-FR-012: Instrument Filtering

The dashboard SHALL support filtering by trading instrument:

- Multi-select dropdown listing all instruments the user has traded.
- Default: all instruments selected.
- Instrument list SHALL be dynamically populated from the user's trade history.
- Display format: Symbol + Name (e.g., "CL - Crude Oil", "GC - Gold", "MES - Micro E-mini S&P 500").
- "Select All" and "Clear All" convenience buttons.
- Active instrument filters SHALL be displayed as dismissible chips below the filter bar.

#### AN-FR-013: Playbook Filtering

The dashboard SHALL support filtering by playbook:

- Multi-select dropdown listing all playbooks the user has created (PRD-005).
- Default: all playbooks selected.
- Include an "Untagged" option for trades not assigned to any playbook.
- Playbooks SHALL display their trade count next to the name (e.g., "A+ Trendline Break (47)").

#### AN-FR-014: Combined Filter Logic

- All filters (date range, instrument, playbook) SHALL apply simultaneously using AND logic.
- Example: Date Range = "90 Days" AND Instrument = "CL" AND Playbook = "A+ Trendline Break" shows only A+ Trendline Break trades on Crude Oil in the last 90 days.
- The total trade count matching current filters SHALL be displayed in the filter bar (e.g., "Showing 23 of 156 trades").
- If combined filters result in zero trades, all widgets SHALL display their empty state.
- A "Clear All Filters" button SHALL reset to defaults (30 Days, all instruments, all playbooks).

### 3.4 Chart Visualizations

#### AN-FR-015: Equity Curve Chart

The equity curve SHALL display cumulative P&L over time as a line chart:

- X-axis: date (trade exit dates). Y-axis: cumulative P&L in dollars.
- Line color: green when above starting equity, red when below.
- Gradient fill below the line (green gradient above zero, red gradient below zero).
- Hover tooltip: date, cumulative P&L, daily P&L, trade count for that day.
- Benchmark line: horizontal line at $0 (breakeven).
- Annotations: clickable markers at max drawdown start and end, largest single-day P&L.
- Zoom: click-and-drag to zoom into a date range. Double-click to reset zoom.
- The chart SHALL update in real-time via WebSocket when a new trade closes.

**Comparative Mode (Pro Tier, see AN-FR-032):**
- Overlay multiple equity curves: paper vs. live, playbook A vs. B, period vs. period.
- Each curve in a distinct color with legend.

#### AN-FR-016: P&L Calendar Heatmap

The P&L calendar heatmap SHALL display daily P&L as a color-coded calendar grid:

- Layout: GitHub-style contribution heatmap with weeks as columns and days as rows.
- Color scale: dark red (worst day) through light red, white (no trades), light green through dark green (best day).
- Cell tooltip on hover: date, net P&L, trade count, win rate for that day.
- Click on any day SHALL drill down to show a list of individual trades for that date with: instrument, direction, playbook, P&L, R-multiple.
- Trade list in drill-down SHALL link to the full journal entry (PRD-004).
- Navigation: month-by-month or scroll through calendar view.
- The heatmap SHALL show the current month and the previous 11 months by default (12 months total).
- Summary row at bottom: monthly totals for net P&L, trade count, win rate.

#### AN-FR-017: R-Multiple Distribution Histogram

The R-multiple histogram SHALL display the distribution of trade outcomes in R-multiple units:

- X-axis: R-multiple bins (e.g., -3R to -2R, -2R to -1R, -1R to 0R, 0R to 1R, 1R to 2R, 2R to 3R, 3R+).
- Y-axis: trade count.
- Bin width: 0.5R (configurable between 0.25R and 1R).
- Bar color: red for negative R bins, green for positive R bins.
- Overlay: vertical line at average R, vertical line at median R, labeled.
- Hover tooltip: R-range, trade count, percentage of total trades.
- Click on a bin SHALL filter the trade list below to show only trades in that R-range.
- Display summary stats above chart: Average R, Median R, Std Dev of R, Skewness.

#### AN-FR-018: Win Rate by Dimension Charts

The system SHALL display win rate broken down by multiple dimensions as bar charts or tables:

| Dimension | Chart Type | Notes |
|---|---|---|
| By Instrument | Horizontal bar chart | Sorted by trade count descending |
| By Day of Week | Vertical bar chart | Mon-Fri fixed order |
| By Hour of Day | Vertical bar chart | 0-23 fixed order |
| By Playbook | Horizontal bar chart | Sorted by trade count descending |
| By Month | Vertical bar chart | Jan-Dec or chronological |
| By Setup Type | Horizontal bar chart | Break vs. Bounce |

- Each bar SHALL be labeled with win rate percentage and trade count.
- Bars with fewer than 5 trades SHALL be visually distinguished (hatched or semi-transparent) with a "low sample size" indicator.
- The user SHALL be able to switch between "Win Rate," "Average R," and "Net P&L" as the displayed metric using a toggle.

#### AN-FR-019: MAE/MFE Scatter Plots

The MAE/MFE analysis SHALL display two scatter plots:

**MAE Scatter Plot:**
- X-axis: MAE (maximum adverse excursion) in R-multiples or ticks (toggle).
- Y-axis: trade outcome in R-multiples or P&L (toggle).
- Each dot = one trade. Green dots = winners, red dots = losers.
- Vertical reference line at current stop loss distance (1R).
- Insight callout: "X% of your winners had MAE > 0.5R" (indicating stop placement optimization potential).

**MFE Scatter Plot:**
- X-axis: MFE (maximum favorable excursion) in R-multiples or ticks (toggle).
- Y-axis: trade outcome in R-multiples or P&L (toggle).
- Each dot = one trade. Green dots = winners, red dots = losers.
- Diagonal reference line: MFE = outcome (trades that captured 100% of favorable move).
- Insight callout: "On average, you capture X% of the maximum favorable move."

**Combined MAE/MFE Table:**
- Tabular view showing: trade date, instrument, playbook, entry price, exit price, MAE (ticks), MAE ($), MFE (ticks), MFE ($), outcome (R), outcome ($).
- Sortable by any column. Filterable by winners/losers.

#### AN-FR-020: Drawdown Chart (Underwater Equity Curve)

The drawdown chart SHALL display the equity curve's drawdown from peak as a filled area chart:

- X-axis: date. Y-axis: drawdown from peak (negative values, displayed as positive for readability, e.g., "5% drawdown").
- Fill color: red gradient, darker red for deeper drawdowns.
- Hover tooltip: date, drawdown amount ($), drawdown percentage (%), days since peak, current equity, peak equity.
- Annotations at each drawdown trough: drawdown magnitude and recovery time (or "ongoing").
- Display table below chart listing all drawdown periods:

| # | Start Date | Trough Date | Recovery Date | Depth ($) | Depth (%) | Duration (days) | Recovery (days) |
|---|---|---|---|---|---|---|---|
| 1 | 2026-01-05 | 2026-01-12 | 2026-01-20 | -$2,400 | -8.3% | 7 | 8 |
| 2 | 2026-01-25 | 2026-02-01 | Ongoing | -$1,800 | -5.9% | 7 | Ongoing |

#### AN-FR-021: Time-Based Analysis Charts

The system SHALL display time analysis as grouped bar charts:

**P&L by Hour of Day:**
- 24 bars (0-23), each showing net P&L for trades entered during that hour.
- Dual axis: bar height = net P&L, overlaid line = trade count.
- Exchange timezone label displayed.

**P&L by Day of Week:**
- 5 bars (Monday-Friday), each showing net P&L.
- Dual axis: bar height = net P&L, overlaid line = win rate.
- Color coding: green for net positive days, red for net negative.

**P&L by Month:**
- 12 bars (Jan-Dec) or chronological months, each showing net P&L.
- Dual axis: bar height = net P&L, overlaid line = trade count.
- Toggleable between calendar year aggregate (all Januaries combined) and chronological (Jan 2025, Feb 2025, ...).

#### AN-FR-022: Session Analysis (RTH vs. Overnight)

The session analysis SHALL display a side-by-side comparison:

| Metric | RTH | Overnight |
|---|---|---|
| Trade Count | [value] | [value] |
| Win Rate | [value] | [value] |
| Net P&L | [value] | [value] |
| Average R | [value] | [value] |
| Profit Factor | [value] | [value] |
| Average Slippage | [value] | [value] |

- Visual: two equity curves overlaid (RTH in blue, overnight in orange) showing cumulative P&L for each session type.
- Insight callout if one session significantly outperforms: "Your RTH trades outperform overnight by $X (Y% higher win rate)."

#### AN-FR-023: Execution Quality Dashboard

The execution quality section SHALL display:

- **Slippage Distribution:** Histogram of slippage values (in ticks) across all trades. X-axis: slippage bins, Y-axis: trade count.
- **Slippage Over Time:** Line chart showing rolling average slippage (20-trade window) over time. Trend detection: alert if slippage is increasing.
- **Fill Quality Score:** Gauge chart (0-100) with color coding (80-100: excellent, 60-79: good, 40-59: fair, <40: poor).
- **Slippage by Instrument Table:** Sortable table with instrument, avg slippage (ticks), avg slippage ($), trade count.
- **Slippage by Order Type:** Market vs. limit order slippage comparison.

#### AN-FR-024: Behavioral Metrics Dashboard

The behavioral section SHALL display:

- **Tiltmeter Gauge:** Circular gauge, 0-100, with color zones (green/yellow/orange/red), current score prominently displayed.
- **Rule Compliance Trend:** Line chart showing rule compliance rate over rolling 20-trade windows.
- **Cost of Mistakes Waterfall:** Horizontal bar chart showing P&L impact of each mistake type. Bars sorted by absolute cost descending.
- **Mistake Frequency Pie Chart:** Distribution of mistake types as a donut chart with legend.
- **Conviction vs. Outcome Scatter:** Scatter plot with conviction level (1-5) on X-axis, R-multiple on Y-axis. Correlation coefficient displayed.
- **Emotional State P&L:** Bar chart showing net P&L when trading under each emotional state (confident, anxious, FOMO, revenge, patient, disciplined).

#### AN-FR-025: Trendline Analytics Dashboard

The trendline-specific section SHALL display:

- **Win Rate by Touch Count:** Bar chart with touch count categories on X-axis, win rate on Y-axis. Trade count labeled on each bar.
- **Edge by Slope Angle:** Bar chart with slope angle ranges on X-axis, average R-multiple on Y-axis.
- **Performance by Duration:** Bar chart with duration ranges on X-axis, profit factor on Y-axis.
- **Trendline Grade Comparison:** Side-by-side metric cards for A+, A, and B grade trendlines showing win rate, avg R, profit factor, trade count.
- **Break vs. Bounce Comparison:** Same side-by-side format for break vs. bounce setups.
- **Statistical Significance Indicator:** For each segmented metric, display whether the sample size is sufficient for statistical significance (minimum 30 trades per segment for moderate confidence, displayed as a confidence badge: "High Confidence (n=47)" or "Low Confidence (n=8)").

### 3.5 Advanced Analytics (Pro Tier)

#### AN-FR-026: Monte Carlo Simulation

The Monte Carlo simulation engine SHALL:

1. Accept the user's closed trade history (R-multiples) as input.
2. Generate N simulated equity curves (default N=1,000, configurable: 500, 1,000, 5,000, 10,000) by randomly resampling trades with replacement.
3. Each simulated curve uses the same number of trades as the actual history.
4. Display a fan chart showing the following percentile curves: 5th, 25th, 50th (median), 75th, 95th.
5. Overlay the actual equity curve on the simulation fan.
6. Display summary statistics:

| Metric | 5th Percentile | 25th | Median | 75th | 95th |
|---|---|---|---|---|---|
| Final Equity | [value] | [value] | [value] | [value] | [value] |
| Max Drawdown | [value] | [value] | [value] | [value] | [value] |
| Longest Drawdown | [value] | [value] | [value] | [value] | [value] |

7. "Probability of Ruin" calculation: percentage of simulated curves that hit a configurable drawdown threshold (default: 50% of peak equity).
8. The simulation SHALL run server-side via FastAPI endpoint to avoid blocking the UI.
9. Computation time for 1,000 simulations on 500 trades SHALL be under 5 seconds.
10. Results SHALL be cached for 1 hour or until a new trade is added.

**Minimum trade count:** 30 trades required to run Monte Carlo. Display "Minimum 30 closed trades required for Monte Carlo simulation" if insufficient.

#### AN-FR-027: Strategy Correlation Matrix

The strategy correlation matrix SHALL:

1. Calculate the Pearson correlation coefficient of daily returns between each pair of playbooks.
2. Display as a heatmap matrix: playbooks on both axes, cells colored from -1 (dark blue, negative correlation) through 0 (white) to +1 (dark red, positive correlation).
3. Correlation value displayed in each cell on hover.
4. Require a minimum of 20 overlapping trading days between two playbooks to calculate correlation; display "N/A" otherwise.
5. Insight callout: highlight playbook pairs with correlation > 0.7 ("These strategies tend to win and lose together — limited diversification benefit") and pairs with correlation < -0.3 ("These strategies diversify well — losses in one tend to coincide with wins in the other").

#### AN-FR-028: Walk-Forward Analysis

The walk-forward analysis SHALL:

1. Calculate key metrics (win rate, average R, profit factor, Sharpe ratio) on rolling windows of configurable trade counts: 20, 30, 50, 100 trades.
2. Display as a multi-line chart: X-axis = trade number (or date of Nth trade), Y-axis = metric value.
3. Highlight declining trends with red shading when a metric drops below its all-history average for 2+ consecutive windows.
4. Display decay detection alert: "Your [playbook] profit factor has declined from [X] to [Y] over the last [N] trades. Consider reviewing this strategy."
5. Support per-playbook walk-forward analysis (select a single playbook to analyze its evolution).

#### AN-FR-029: Drawdown Analysis (Advanced)

The advanced drawdown analysis SHALL extend AN-FR-020 with:

1. **Drawdown Clustering:** Identify whether drawdowns cluster in time (Ljung-Box test on drawdown periods). Display: "Your drawdowns tend to cluster — consider reducing size after a loss" or "Your drawdowns are randomly distributed."
2. **Time-to-Recovery Distribution:** Histogram of recovery times for all completed drawdowns.
3. **Conditional Drawdown Analysis:** Drawdown statistics segmented by: day of week, instrument, playbook, emotional state.
4. **Drawdown Duration vs. Depth Scatter:** Each drawdown as a point, X = duration (days), Y = depth ($). Identify outliers.

#### AN-FR-030: AI-Powered Insights

The AI insights feature SHALL:

1. Provide a chat interface within the analytics dashboard.
2. Accept natural language queries about the user's trading data.
3. Translate queries into SQL or analytical operations against the user's trade data.
4. Return answers in natural language with supporting data tables and/or inline charts.
5. Example queries and expected behavior:

| Query | Expected Response |
|---|---|
| "What is my best setup on Tuesdays in crude oil?" | "Your best-performing Tuesday setup in CL is A+ Trendline Break with a 75% win rate and 2.1R average across 12 trades." |
| "Show me all losing trades where I moved my stop" | Table of trades tagged with "moved stop" mistake AND negative P&L, sorted by P&L ascending. |
| "Compare my morning vs. afternoon performance" | Side-by-side metrics for trades entered before 12:00 vs. after 12:00 exchange time. |
| "Am I getting worse at crude oil?" | Walk-forward analysis of CL trades showing trend in key metrics. |
| "What would happen if I only traded A+ setups?" | Filtered equity curve and metrics for A+ playbook trades only, compared to all-trade curve. |

6. The system SHALL use Claude API (Anthropic) for natural language understanding and response generation.
7. Query context SHALL include the user's trade schema, available fields, and current filter state.
8. The system SHALL NOT expose raw trade data to the AI model beyond what is necessary to answer the query. Aggregate statistics are preferred over row-level data where possible.
9. Rate limit: 20 AI queries per day on Pro tier, 50 on Team tier.
10. Query history SHALL be saved and searchable.

#### AN-FR-031: P&L Calendar Heatmap Enhancements (Pro)

The Pro-tier P&L calendar SHALL add:

1. **Weekly and Monthly Aggregation:** Toggle between daily, weekly, and monthly heatmap granularity.
2. **Multi-Metric Heatmap:** Switch the heatmap color metric between Net P&L, R-Multiple, Win Rate, and Trade Count.
3. **Year-over-Year Comparison:** Side-by-side calendar views for two selected years.
4. **Goal Tracking Overlay:** User sets a daily/weekly/monthly P&L goal; calendar cells show green check for days meeting goal, red X for days missing goal.

#### AN-FR-032: Comparative Analytics

The comparative analytics system SHALL support:

**Paper vs. Live Comparison:**
1. Side-by-side equity curves: paper trades (dashed line) and live trades (solid line).
2. Metric comparison table showing all core metrics for paper and live separately.
3. Statistical test (two-sample t-test) on mean R-multiples: "Your live trading R-multiples are statistically different from paper trading (p < 0.05)" or "No significant difference detected."

**Period vs. Period Comparison:**
1. User selects two custom date ranges (Period A and Period B).
2. Side-by-side metric comparison table.
3. Overlaid equity curves normalized to start at $0.
4. Highlight metrics that improved or degraded by more than 10%.

**Strategy A vs. B Comparison:**
1. User selects two playbooks.
2. Side-by-side metric comparison table.
3. Overlaid equity curves normalized to start at $0.
4. Correlation coefficient between the two strategies' daily returns.

**Month-over-Month Comparison:**
1. Automatic comparison of current month vs. previous month.
2. Sparkline trend for each metric showing last 6 months.
3. Percentage change indicators (green up arrow for improvement, red down arrow for degradation).

### 3.6 Export and Reporting

#### AN-FR-033: Dashboard Export (PDF Report)

The PDF export system SHALL:

1. Generate a multi-page PDF report reflecting the current dashboard state (all active filters applied).
2. Report sections:
   - **Cover Page:** TrendEdge logo, user name, date range, generation timestamp.
   - **Executive Summary:** Key metrics (net P&L, win rate, profit factor, Sharpe ratio, max drawdown) in a summary card layout.
   - **Equity Curve:** Full-width chart rendering.
   - **P&L Calendar:** Calendar heatmap for the selected period.
   - **Performance Breakdown:** Tables for all metric categories.
   - **Chart Pages:** R-multiple histogram, MAE/MFE scatter, drawdown chart, time analysis, win rate by dimension.
   - **Trendline Analytics:** Trendline-specific metrics and charts (if applicable).
   - **Advanced Analytics:** Monte Carlo results, correlation matrix (if Pro tier and data available).
3. PDF SHALL be generated server-side using WeasyPrint or Playwright's PDF rendering.
4. Maximum generation time: 30 seconds for a complete report.
5. The user SHALL receive a progress indicator during generation.
6. Completed PDFs SHALL be available for download for 24 hours, stored in Cloudflare R2.
7. PDF file name format: `TrendEdge_Performance_Report_{YYYY-MM-DD}_{range}.pdf`

#### AN-FR-034: Data Export (CSV)

The system SHALL support CSV export of:

1. Complete trade list with all computed metrics (R-multiple, MAE, MFE, slippage).
2. Daily P&L summary.
3. Metric summary for the selected period.
4. Export SHALL respect current filter selections.
5. CSV encoding: UTF-8 with BOM for Excel compatibility.
6. Maximum export size: 50,000 rows.

### 3.7 Real-Time Updates

#### AN-FR-035: WebSocket Dashboard Updates

The dashboard SHALL receive real-time updates via WebSocket:

1. When a new trade is closed (fill confirmed from broker), the server SHALL:
   a. Recalculate affected metrics (all metrics in the current filter scope).
   b. Publish updated metric values to the user's WebSocket channel.
   c. The frontend SHALL update all affected widgets without a full page reload.
2. Update event payload:

```json
{
  "type": "trade_closed",
  "trade_id": "uuid",
  "timestamp": "2026-02-11T14:30:00Z",
  "updates": {
    "net_pnl": 15420.50,
    "win_rate": 63.2,
    "total_trades": 156,
    "equity_curve_point": { "date": "2026-02-11", "cumulative_pnl": 15420.50 },
    "tiltmeter": 22
  }
}
```

3. The frontend SHALL animate metric changes (count-up animation for numbers, smooth curve extension for charts).
4. A "Last Updated" timestamp SHALL be displayed in the dashboard header.
5. If the WebSocket connection drops, the dashboard SHALL:
   a. Display a "Connection lost — reconnecting..." banner.
   b. Attempt reconnection with exponential backoff (1s, 2s, 4s, 8s, 16s, max 30s).
   c. On reconnection, fetch the latest state via REST API to ensure consistency.

### 3.8 Tier Restrictions

#### AN-FR-036: Free Tier Limitations

The Free tier SHALL be limited to:

1. **5 Basic Metrics:** Total Net P&L, Win Rate, Total Trades, Average Winner, Average Loser.
2. **Basic Equity Curve:** Simple line chart without annotations, zoom, or comparative overlays.
3. **No filtering:** Default date range (all-time) only. No instrument, playbook, or custom date filters.
4. **No chart drill-down:** Calendar heatmap, histograms, and scatter plots are NOT available.
5. **No export:** PDF and CSV export are NOT available.
6. **Upgrade prompts:** Locked widgets SHALL display a blurred preview of the chart/metric with an "Upgrade to Trader" call-to-action overlay.

#### AN-FR-037: Trader Tier ($49/month)

The Trader tier SHALL include:

1. All 25+ core metrics across all 7 categories (AN-FR-001 through AN-FR-007).
2. Full dashboard with all chart visualizations (AN-FR-015 through AN-FR-025).
3. All filtering options (date range, instrument, playbook, combined).
4. P&L calendar heatmap with drill-down.
5. Dashboard customization (reorder, hide/show, 5 layout presets).
6. CSV export.
7. PDF export (up to 2 reports per month).

#### AN-FR-038: Pro Tier ($99/month)

The Pro tier SHALL include everything in Trader, plus:

1. Monte Carlo simulation (AN-FR-026).
2. Strategy correlation matrix (AN-FR-027).
3. Walk-forward analysis (AN-FR-028).
4. Advanced drawdown analysis (AN-FR-029).
5. AI-powered insights with 20 queries/day (AN-FR-030).
6. Enhanced P&L calendar with goal tracking (AN-FR-031).
7. Comparative analytics: paper vs. live, period vs. period, strategy A vs. B (AN-FR-032).
8. Unlimited PDF exports.
9. Unlimited layout presets.

#### AN-FR-039: Team Tier ($199/month)

The Team tier SHALL include everything in Pro, plus:

1. Team-level aggregated dashboard: combined metrics across all team members.
2. Individual member drill-down from team view.
3. Team leaderboard: ranked by configurable metric (net P&L, win rate, Sharpe ratio, avg R).
4. Team-wide strategy correlation (which team members' trades correlate).
5. Manager view: compare any two team members side-by-side.
6. 50 AI queries/day.
7. Shared layout presets across team.
8. Team export: combined PDF report across selected members.
9. Maximum team size: 25 members.

---

## 4. Non-Functional Requirements

#### AN-NFR-001: Dashboard Load Time

- Initial dashboard load (all widgets with data) SHALL complete in under 3 seconds on a broadband connection (10+ Mbps) for users with up to 1,000 trades.
- For users with 1,000-10,000 trades, initial load SHALL complete in under 5 seconds.
- Subsequent navigation (filter changes, date range changes) SHALL update widgets in under 2 seconds.
- Strategy: use materialized views in PostgreSQL for pre-computed aggregations; lazy-load below-the-fold widgets; cache computed metrics in Redis with 5-minute TTL.

#### AN-NFR-002: Metrics Recalculation Performance

- When a new trade is closed, all affected metrics SHALL be recalculated and pushed to the dashboard within 5 seconds.
- Recalculation SHALL use incremental computation where possible (e.g., updating running averages) rather than full recomputation.
- Full recomputation (triggered by filter change or data correction) SHALL complete within 10 seconds for 10,000 trades.

#### AN-NFR-003: Data Volume Support

- The system SHALL support up to 10,000 closed trades per user without degradation of dashboard performance.
- The system SHALL support up to 50,000 closed trades per user with graceful degradation (load time up to 8 seconds acceptable).
- For users exceeding 50,000 trades, the system SHALL paginate trade-level views and warn that some chart visualizations may be slow.
- Database indexes SHALL be maintained on: user_id, exit_timestamp, instrument, playbook_id, and compound indexes for common filter combinations.

#### AN-NFR-004: Chart Rendering Performance

- All charts SHALL render within 500ms after data is received by the frontend.
- Charts with more than 5,000 data points (e.g., equity curve with daily points over 15+ years) SHALL use data downsampling (Largest Triangle Three Buckets algorithm) to maintain rendering performance while preserving visual fidelity.
- Chart animations (transitions, tooltips) SHALL run at 60fps.
- Charts SHALL use canvas rendering (via Recharts/D3) instead of SVG for datasets exceeding 1,000 points.

#### AN-NFR-005: Mobile Responsiveness

- The dashboard SHALL be fully functional on viewports 375px and wider (iPhone SE and above).
- Touch targets SHALL be at least 44x44px per Apple Human Interface Guidelines.
- Charts SHALL support touch gestures: pinch-to-zoom, swipe-to-pan, tap-for-tooltip.
- The mobile layout SHALL prioritize summary metrics and equity curve, with other widgets accessible via vertical scroll.
- No horizontal scrolling SHALL be required on mobile viewports (except for data tables, which may scroll horizontally within their container).

#### AN-NFR-006: Accessibility

- All charts SHALL have text-based alternatives (data tables accessible via a toggle).
- Color usage SHALL not be the sole means of conveying information; patterns, labels, or icons SHALL supplement color coding.
- The dashboard SHALL meet WCAG 2.1 AA compliance for contrast ratios (minimum 4.5:1 for normal text, 3:1 for large text).
- All interactive elements SHALL be keyboard navigable.
- Screen reader support for metric values and summary statistics.

#### AN-NFR-007: Browser Support

- The dashboard SHALL support the latest two major versions of: Chrome, Firefox, Safari, Edge.
- Mobile browsers: Safari (iOS 16+), Chrome (Android 12+).
- WebSocket support is required; browsers without WebSocket SHALL fall back to polling (30-second interval).

#### AN-NFR-008: API Rate Limiting

- Dashboard API endpoints SHALL enforce rate limits per user:
  - Metrics endpoints: 60 requests/minute.
  - Chart data endpoints: 30 requests/minute.
  - Export endpoints: 5 requests/hour.
  - AI query endpoint: per-tier daily limits (see AN-FR-030).
- Rate limit responses SHALL return HTTP 429 with a `Retry-After` header.

#### AN-NFR-009: Data Freshness

- Cached metric values SHALL have a maximum staleness of 5 minutes under normal operation.
- WebSocket-pushed updates SHALL reflect trades closed within the last 5 seconds.
- The dashboard SHALL display a "Data as of [timestamp]" indicator.
- A manual "Refresh" button SHALL force cache invalidation and full recomputation.

#### AN-NFR-010: Availability

- The analytics dashboard SHALL target 99.5% uptime (approximately 1.8 days downtime per year).
- Degraded mode: if the computation backend is unavailable, the dashboard SHALL display the last cached metric values with a "Data may be stale" warning.
- Chart rendering is client-side and SHALL remain functional even if the API is temporarily unreachable (using locally cached data from the last successful fetch).

---

## 5. Dependencies

### 5.1 PRD-003: Trade Execution Pipeline

| Dependency | Data Required | Impact if Unavailable |
|---|---|---|
| Closed trade records | Entry/exit timestamps, prices, fills, P&L, commissions | No analytics possible — core data source |
| MAE/MFE tick data | Tick-by-tick or bar-by-bar price data during trade holding period | MAE/MFE analysis unavailable; estimated from bar data |
| Signal price | Original signal price for slippage calculation | Slippage metrics show "N/A" |
| Trendline metadata | Touch count, slope, duration, grade, spacing attached to trade | Trendline-specific analytics section empty |
| Broker order data | Order type, broker ID, fill timestamps | Execution quality metrics incomplete |
| Paper/live flag | Whether trade was executed in paper or live mode | Paper vs. live comparison unavailable |

### 5.2 PRD-004: Trade Journaling

| Dependency | Data Required | Impact if Unavailable |
|---|---|---|
| Conviction level | 1-5 scale per trade | Conviction vs. outcome correlation unavailable |
| Emotional state tags | Array of emotional state labels per trade | Emotional state P&L analysis unavailable |
| Mistake tags | Array of mistake labels per trade | Cost of mistakes, mistake breakdown unavailable |
| Rule compliance | Boolean per trade (did trader follow playbook rules) | Rule compliance rate unavailable |
| Session classification | RTH vs. overnight based on entry time | Session analysis defaults to computed value from trade timestamp |

### 5.3 PRD-005: Playbook System

| Dependency | Data Required | Impact if Unavailable |
|---|---|---|
| Playbook assignment | Each trade's playbook_id | Playbook filtering and per-playbook analytics unavailable |
| Playbook definitions | Playbook names and criteria descriptions | Playbook filter dropdown empty |
| Auto-classification | Automatic playbook tagging from trendline metadata | Trades appear as "Untagged" in playbook analytics |

### 5.4 External Dependencies

| Dependency | Provider | Purpose | Fallback |
|---|---|---|---|
| PostgreSQL | Supabase | Trade data storage, aggregation queries, materialized views | Railway PostgreSQL |
| Redis | Upstash | Metric caching, WebSocket pub/sub | In-memory cache (single-instance only) |
| Claude API | Anthropic | AI-powered insights (AN-FR-030) | Feature disabled with "AI insights temporarily unavailable" message |
| PDF Rendering | WeasyPrint / Playwright | Server-side PDF generation | CSV-only export with message "PDF generation temporarily unavailable" |
| Cloudflare R2 | Cloudflare | Export file storage (24-hour retention) | Local file system with reduced retention |

---

## 6. Testing Requirements

### 6.1 Metrics Calculation Accuracy

#### AN-TEST-001: Known Dataset Verification

Create a reference dataset of 100 trades with manually calculated expected values for every metric. The test dataset SHALL include:

- A mix of winners and losers (approximately 55% win rate).
- Trades across 5 instruments (CL, GC, PL, YM, MES).
- Trades across 3 playbooks (A+ Break, Standard Break, Bounce).
- Trades with varying R-multiples from -3R to +5R.
- Trades across all days of week and multiple hours.
- Trades in both RTH and overnight sessions.
- Trades with and without mistake tags, emotional state tags, and conviction levels.
- At least 5 trades with MAE/MFE data.
- At least 3 drawdown periods with known depths and recovery times.

**Assertions (exact match or within tolerance):**

| Metric | Tolerance |
|---|---|
| Win Rate | Exact match (equal number of decimal places) |
| Average Winner / Loser | Within $0.01 |
| Profit Factor | Within 0.01 |
| Expectancy | Within $0.01 |
| Sharpe Ratio | Within 0.01 |
| Sortino Ratio | Within 0.01 |
| Calmar Ratio | Within 0.01 |
| Max Drawdown ($) | Exact match |
| Max Drawdown (%) | Within 0.01% |
| R-Multiple per trade | Within 0.01R |
| Average R | Within 0.01R |
| Tiltmeter Score | Within 1 point |
| Slippage | Within 0.1 ticks |
| Rule Compliance Rate | Exact match |
| Cost of Mistakes | Within $0.01 |

#### AN-TEST-002: Edge Case Testing

Test the following edge cases:

| Scenario | Expected Behavior |
|---|---|
| User has 0 trades | All metrics display "No data." Equity curve shows empty state. |
| User has 1 trade (winner) | Win rate = 100%. Profit factor = N/A (no losses). Sharpe = "Insufficient data." |
| User has 1 trade (loser) | Win rate = 0%. Profit factor = 0. Sharpe = "Insufficient data." |
| All trades are winners | Profit factor = infinity, displayed as "INF" or ">100". Sortino = "N/A" (no downside deviation). |
| All trades are losers | Profit factor = 0. Win rate = 0%. |
| Trade with $0 P&L (breakeven after commissions) | Classified as a loss per AN-FR-001. |
| Trade with no stop loss defined | R-multiple = "N/A." Excluded from R-based aggregates. |
| Extremely large P&L ($100,000+ single trade) | No overflow. Charts auto-scale Y-axis. |
| Trades spanning midnight (overnight hold) | Correctly attributed to entry date for time analysis. |
| Trades on the same instrument opened simultaneously | Each trade tracked independently. |
| User changes timezone setting | All time-based analysis recalculates with new timezone. |

#### AN-TEST-003: Filter Combination Testing

Test all filter combinations for correctness:

- Date range only (each preset + custom).
- Single instrument filter.
- Multiple instrument filter.
- Single playbook filter.
- Multiple playbook filter.
- Date range + single instrument + single playbook.
- Date range + multiple instruments + multiple playbooks.
- Filters resulting in 0 matching trades.
- Filters resulting in 1 matching trade.
- Changing filters rapidly (debounce behavior).
- Filter state preserved after page refresh (URL parameters).
- Filter state cleared by "Clear All Filters."

### 6.2 Chart Rendering Correctness

#### AN-TEST-004: Visual Regression Testing

Implement visual regression tests using Playwright screenshot comparison for:

- Equity curve with known data points (verify line follows expected path).
- P&L calendar heatmap with known daily P&L (verify correct color assignments).
- R-multiple histogram with known distribution (verify correct bin counts and bar heights).
- MAE/MFE scatter plot with known data points (verify dot positions).
- Drawdown chart with known drawdown periods (verify fill area covers correct date ranges).
- All charts in empty state.
- All charts in single-data-point state.
- All charts at mobile viewport width (375px).
- All charts at tablet viewport width (768px).

#### AN-TEST-005: Chart Interactivity Testing

- Verify tooltip appears on hover with correct values for each chart type.
- Verify calendar drill-down shows correct trades for the clicked date.
- Verify histogram bin click filters to correct trades.
- Verify equity curve zoom (click-and-drag) and reset (double-click) work correctly.
- Verify chart full-screen mode renders correctly and exits cleanly.

### 6.3 Performance Benchmarking

#### AN-TEST-006: Load Testing

| Scenario | Dataset Size | Target Load Time |
|---|---|---|
| Small account | 50 trades | <1 second |
| Medium account | 500 trades | <2 seconds |
| Standard account | 2,000 trades | <3 seconds |
| Large account | 10,000 trades | <5 seconds |
| Very large account | 50,000 trades | <8 seconds |

- Load time measured from navigation start to all above-the-fold widgets rendered with data (Largest Contentful Paint + data fetch).
- Test with cold cache (no Redis cache) and warm cache (pre-cached metrics).
- Test with concurrent users: 10, 50, 100 simultaneous dashboard loads.

#### AN-TEST-007: Monte Carlo Performance

| Scenario | Simulations | Trades | Target Time |
|---|---|---|---|
| Standard | 1,000 | 100 | <2 seconds |
| Standard | 1,000 | 500 | <5 seconds |
| Large | 5,000 | 500 | <15 seconds |
| Maximum | 10,000 | 1,000 | <30 seconds |

- Verify simulation results are statistically consistent: running the same simulation twice should produce percentile values within 5% of each other.

### 6.4 Export Validation

#### AN-TEST-008: PDF Export Testing

- PDF contains all sections listed in AN-FR-033.
- Charts in PDF visually match on-screen charts (visual comparison).
- PDF renders correctly in Adobe Reader, Chrome PDF viewer, and macOS Preview.
- PDF file size is under 10MB for a standard report.
- PDF generation completes within 30 seconds for a full report with all charts.
- PDF respects current filter selections (filtered data matches on-screen data).
- Cover page shows correct user name, date range, and generation timestamp.

#### AN-TEST-009: CSV Export Testing

- CSV contains correct headers matching documented field names.
- CSV values match on-screen metric values.
- CSV opens correctly in Excel (UTF-8 BOM handling).
- CSV handles special characters in trade notes (commas, quotes, newlines properly escaped).
- CSV row count matches the filtered trade count displayed in the dashboard.

### 6.5 Tier Restriction Enforcement

#### AN-TEST-010: Tier Access Control

| Feature | Free | Trader | Pro | Team |
|---|---|---|---|---|
| 5 basic metrics | Accessible | Accessible | Accessible | Accessible |
| Full 25+ metrics | Locked | Accessible | Accessible | Accessible |
| Date/instrument/playbook filters | Locked | Accessible | Accessible | Accessible |
| Calendar heatmap with drill-down | Locked | Accessible | Accessible | Accessible |
| Dashboard customization | Locked | Accessible | Accessible | Accessible |
| CSV export | Locked | Accessible | Accessible | Accessible |
| PDF export | Locked | 2/month | Unlimited | Unlimited |
| Monte Carlo | Locked | Locked | Accessible | Accessible |
| Strategy correlation | Locked | Locked | Accessible | Accessible |
| Walk-forward analysis | Locked | Locked | Accessible | Accessible |
| AI insights | Locked | Locked | 20/day | 50/day |
| Comparative analytics | Locked | Locked | Accessible | Accessible |
| Team dashboard | Locked | Locked | Locked | Accessible |

- Verify that accessing a locked feature via direct API call returns HTTP 403 with tier upgrade message.
- Verify that locked widgets show blurred preview with upgrade CTA on the frontend.
- Verify that downgrading from Pro to Trader immediately restricts access to Pro features.
- Verify that PDF export count resets on billing cycle date.
- Verify that AI query count resets at midnight UTC daily.

---

## 7. Security Requirements

### 7.1 User Data Isolation

#### AN-SEC-001: Row-Level Security

- All analytics queries SHALL enforce PostgreSQL Row-Level Security (RLS) policies ensuring users can only access their own trade data.
- RLS policies SHALL be applied at the database level, not solely at the application level.
- The RLS policy for the `trades` table: `auth.uid() = user_id`.
- The RLS policy for materialized views / cached metrics: `auth.uid() = user_id`.
- Team tier: team members SHALL be able to view (read-only) other team members' data ONLY when the team admin has granted permission. The RLS policy SHALL check team membership and permission level.

#### AN-SEC-002: API Authentication

- All analytics API endpoints SHALL require a valid JWT token (Supabase Auth or Clerk).
- The JWT token SHALL be validated on every request; expired tokens SHALL return HTTP 401.
- WebSocket connections SHALL authenticate on connection establishment and re-authenticate if the token expires during the session.

#### AN-SEC-003: Export Access Control

- PDF and CSV exports SHALL only contain data belonging to the authenticated user.
- Export download URLs SHALL be signed with a time-limited token (24-hour expiry).
- Export URLs SHALL not be guessable (UUID-based, not sequential).
- Export files SHALL be deleted from storage after 24 hours via a scheduled cleanup job.
- Team tier exports: a team member SHALL not be able to export another member's data unless the team admin has granted export permission.

### 7.2 Data Protection

#### AN-SEC-004: Data in Transit

- All API communication SHALL use HTTPS (TLS 1.2+).
- WebSocket connections SHALL use WSS (WebSocket Secure).
- No trade data SHALL be transmitted in URL query parameters (use POST bodies for data queries).

#### AN-SEC-005: Data at Rest

- Trade data in PostgreSQL SHALL be encrypted at rest (Supabase default: AES-256).
- Export files in Cloudflare R2 SHALL be stored with server-side encryption.
- Redis cache entries SHALL NOT contain full trade details; cache keys SHALL be user-scoped (e.g., `metrics:{user_id}:{filter_hash}`).

#### AN-SEC-006: AI Query Security

- Trade data sent to the Claude API for AI-powered insights SHALL be minimized to the fields necessary for answering the query.
- The system SHALL NOT send personally identifiable information (email, name, broker credentials) to the AI API.
- AI query logs SHALL be retained for 30 days for debugging, then purged.
- Users SHALL be informed that AI queries are processed by a third-party AI service (disclosure in settings and first-use consent).

---

## 8. Phase Mapping

### Phase 1: Basic Analytics (Weeks 7-8)

**Scope:** Deliver the minimum viable analytics dashboard alongside the initial Next.js frontend.

| Requirement | Description | Priority |
|---|---|---|
| AN-FR-001 (partial) | 5 basic metrics: Total Net P&L, Win Rate, Total Trades, Average Winner, Average Loser | P0 |
| AN-FR-015 (basic) | Basic equity curve: simple line chart of cumulative P&L over time, no annotations or zoom | P0 |
| AN-FR-008 (basic) | Single-page layout: summary stat cards + equity curve | P0 |
| AN-NFR-001 (relaxed) | Dashboard load under 5 seconds (simpler computation) | P0 |

**Deliverables:**
- FastAPI endpoint: `GET /api/v1/analytics/summary` returning 5 basic metrics.
- FastAPI endpoint: `GET /api/v1/analytics/equity-curve` returning time-series data.
- Next.js page: `/dashboard/analytics` with summary cards and Recharts line chart.
- PostgreSQL queries for metric computation (no materialized views yet).

**Not included in Phase 1:** Filtering, advanced metrics, chart interactivity, exports, WebSocket updates.

### Phase 2: Full Dashboard and Advanced Analytics (Weeks 11-12)

**Scope:** Deliver the complete 25+ metric dashboard with all chart visualizations, filtering, and Pro-tier advanced analytics.

| Requirement | Description | Priority |
|---|---|---|
| AN-FR-001 through AN-FR-007 | All 7 metric categories, 30+ individual metrics | P0 |
| AN-FR-008 through AN-FR-010 | Full dashboard layout, widget system, customization | P0 |
| AN-FR-011 through AN-FR-014 | Complete filtering system (date, instrument, playbook) | P0 |
| AN-FR-015 through AN-FR-025 | All chart visualizations with full interactivity | P0 |
| AN-FR-026 | Monte Carlo simulation (Pro tier) | P1 |
| AN-FR-027 | Strategy correlation matrix (Pro tier) | P1 |
| AN-FR-028 | Walk-forward analysis (Pro tier) | P1 |
| AN-FR-029 | Advanced drawdown analysis (Pro tier) | P1 |
| AN-FR-030 | AI-powered insights (Pro tier) | P1 |
| AN-FR-031 | Enhanced P&L calendar (Pro tier) | P1 |
| AN-FR-032 | Comparative analytics (Pro tier) | P1 |
| AN-FR-033 | PDF export | P1 |
| AN-FR-034 | CSV export | P0 |
| AN-FR-035 | WebSocket real-time updates | P1 |
| AN-FR-036 through AN-FR-038 | Tier restrictions (Free, Trader, Pro) | P0 |
| AN-NFR-001 through AN-NFR-010 | All non-functional requirements at full targets | P0 |
| AN-SEC-001 through AN-SEC-006 | All security requirements | P0 |

**Deliverables:**
- FastAPI analytics service with endpoints for each metric category, chart data, filtering, export, and WebSocket.
- PostgreSQL materialized views for pre-computed aggregations.
- Redis caching layer for computed metrics.
- Next.js analytics dashboard with full widget system, Recharts/D3 charts, filter bar, and export controls.
- Monte Carlo simulation engine (Python, NumPy-based).
- Claude API integration for AI insights.
- PDF generation service.
- Comprehensive test suite (AN-TEST-001 through AN-TEST-010).

### Phase 3: Team Analytics (Weeks 19-20)

**Scope:** Deliver team-level analytics for the Team tier.

| Requirement | Description | Priority |
|---|---|---|
| AN-FR-039 | Team dashboard: aggregated metrics, member drill-down, leaderboard, manager comparison view | P1 |
| AN-SEC-001 (team extension) | Team-aware RLS policies with permission levels | P0 |

**Deliverables:**
- Team analytics API endpoints with team-scoped queries.
- Team dashboard UI: aggregate view, member list, drill-down navigation.
- Team leaderboard component.
- Team-level comparative analytics.
- Team export functionality.
- RLS policy updates for team data access.

---

## 9. Acceptance Criteria

### 9.1 Phase 1 Acceptance Criteria

**AC-AN-001: Basic Metrics Display**
- Given a user with 10+ closed trades in the system
- When the user navigates to `/dashboard/analytics`
- Then within 5 seconds, the page displays: Total Net P&L, Win Rate, Total Trades, Average Winner, and Average Loser
- And all values match manual calculation from the user's trade data (verified against AN-TEST-001 reference dataset)

**AC-AN-002: Equity Curve Rendering**
- Given a user with 10+ closed trades spanning at least 7 days
- When the user views the analytics dashboard
- Then an equity curve line chart renders showing cumulative P&L over time
- And the curve starts at $0 on the date of the first trade
- And each data point corresponds to the cumulative P&L after each trade's exit date
- And the chart renders within 500ms of data receipt

**AC-AN-003: Empty State**
- Given a user with 0 closed trades
- When the user navigates to `/dashboard/analytics`
- Then all metric cards display "No data"
- And the equity curve displays: "Complete your first trade to see your equity curve"
- And no JavaScript errors appear in the console

### 9.2 Phase 2 Acceptance Criteria

**AC-AN-004: Full Metrics Accuracy**
- Given the AN-TEST-001 reference dataset loaded for a test user
- When each metric is computed
- Then all 30+ metrics match expected values within documented tolerances
- And edge cases (AN-TEST-002) produce the documented expected behavior

**AC-AN-005: Filter Functionality**
- Given a user with trades across 3+ instruments and 2+ playbooks over 90+ days
- When the user selects Date Range = "30 Days" AND Instrument = "CL" AND Playbook = "A+ Trendline Break"
- Then all visible metrics and charts update to reflect only matching trades
- And the trade count indicator shows the correct number of matching trades
- And clearing all filters restores the full dataset view

**AC-AN-006: Calendar Drill-Down**
- Given a user viewing the P&L calendar heatmap
- When the user clicks on a date cell with trades
- Then a panel appears listing each trade on that date with: instrument, direction, playbook, P&L, R-multiple
- And clicking a trade in the list navigates to the full journal entry (PRD-004)

**AC-AN-007: Monte Carlo Simulation**
- Given a Pro tier user with 50+ closed trades
- When the user runs a Monte Carlo simulation with 1,000 iterations
- Then within 5 seconds, a fan chart renders with 5th, 25th, 50th, 75th, and 95th percentile curves
- And the actual equity curve is overlaid
- And summary statistics (final equity, max drawdown, probability of ruin) are displayed
- And a Free/Trader tier user attempting the same action sees a locked widget with upgrade prompt

**AC-AN-008: AI-Powered Query**
- Given a Pro tier user with 100+ closed trades including CL trades with playbook tags
- When the user types "What is my best setup in crude oil?" into the AI insights chat
- Then within 10 seconds, a natural language response is returned identifying the highest-performing playbook for CL trades
- And the response includes supporting data (win rate, avg R, trade count)
- And the response is factually accurate against the user's actual trade data

**AC-AN-009: Real-Time Update**
- Given a user with the analytics dashboard open in their browser
- When a new trade is closed via the execution pipeline
- Then within 5 seconds, the summary metric cards update to reflect the new trade
- And the equity curve extends with the new data point
- And no full page reload occurs

**AC-AN-010: PDF Export**
- Given a Trader or Pro tier user viewing the analytics dashboard with filters applied
- When the user clicks "Export PDF"
- Then a progress indicator appears
- And within 30 seconds, a PDF file is available for download
- And the PDF contains all sections listed in AN-FR-033
- And the PDF data matches the on-screen filtered data
- And the PDF renders correctly in standard PDF viewers

**AC-AN-011: Tier Enforcement**
- Given a Free tier user
- When the user views the analytics dashboard
- Then only 5 basic metrics and a basic equity curve are visible
- And all other widgets display blurred previews with "Upgrade to Trader" overlays
- And direct API calls to locked endpoints return HTTP 403
- And upgrading to Trader immediately unlocks the full 25+ metric dashboard without requiring a page reload (WebSocket-triggered entitlement update)

**AC-AN-012: Mobile Responsiveness**
- Given a user accessing the analytics dashboard on a 375px-wide viewport
- When the page loads
- Then all content is visible without horizontal scrolling
- And summary metrics display as a horizontally scrollable carousel
- And charts render at full width with touch-friendly interactions
- And all touch targets are at least 44x44px

### 9.3 Phase 3 Acceptance Criteria

**AC-AN-013: Team Dashboard**
- Given a Team tier admin with 5 team members who have trading data
- When the admin navigates to the team analytics dashboard
- Then aggregated metrics are displayed for the entire team
- And a leaderboard ranks team members by the selected metric
- And clicking a team member drills down to their individual analytics dashboard
- And a non-team-member attempting to access the team dashboard via direct URL receives HTTP 403

**AC-AN-014: Team Data Isolation**
- Given a Team tier with members A and B, where the admin has NOT granted cross-view permission
- When member A attempts to access member B's analytics via API
- Then the request returns HTTP 403
- And when the admin grants cross-view permission and member A retries
- Then member A can view (read-only) member B's analytics

---

## Appendix A: API Endpoint Summary

| Endpoint | Method | Description | Tier |
|---|---|---|---|
| `/api/v1/analytics/summary` | GET | Core metrics summary (5 or 25+ based on tier) | Free+ |
| `/api/v1/analytics/equity-curve` | GET | Equity curve data points | Free+ |
| `/api/v1/analytics/calendar` | GET | P&L calendar heatmap data | Trader+ |
| `/api/v1/analytics/calendar/{date}` | GET | Drill-down trades for a specific date | Trader+ |
| `/api/v1/analytics/r-distribution` | GET | R-multiple histogram data | Trader+ |
| `/api/v1/analytics/win-rate/{dimension}` | GET | Win rate by instrument/day/hour/playbook | Trader+ |
| `/api/v1/analytics/mae-mfe` | GET | MAE/MFE scatter plot data | Trader+ |
| `/api/v1/analytics/drawdown` | GET | Drawdown chart data and drawdown table | Trader+ |
| `/api/v1/analytics/time-analysis` | GET | P&L by hour/day/month data | Trader+ |
| `/api/v1/analytics/session` | GET | RTH vs. overnight comparison | Trader+ |
| `/api/v1/analytics/execution-quality` | GET | Slippage and fill quality metrics | Trader+ |
| `/api/v1/analytics/behavioral` | GET | Rule compliance, tiltmeter, mistake breakdown | Trader+ |
| `/api/v1/analytics/trendline` | GET | Trendline-specific performance breakdown | Trader+ |
| `/api/v1/analytics/monte-carlo` | POST | Run Monte Carlo simulation | Pro+ |
| `/api/v1/analytics/correlation-matrix` | GET | Strategy correlation matrix | Pro+ |
| `/api/v1/analytics/walk-forward` | GET | Walk-forward analysis data | Pro+ |
| `/api/v1/analytics/compare` | POST | Comparative analytics (paper/live, period, strategy) | Pro+ |
| `/api/v1/analytics/ai-query` | POST | AI-powered natural language query | Pro+ |
| `/api/v1/analytics/export/pdf` | POST | Generate PDF report | Trader+ |
| `/api/v1/analytics/export/csv` | GET | Download CSV export | Trader+ |
| `/api/v1/analytics/team/summary` | GET | Team-level aggregated metrics | Team |
| `/api/v1/analytics/team/leaderboard` | GET | Team leaderboard | Team |
| `/api/v1/analytics/team/member/{id}` | GET | Individual team member analytics | Team |
| `/ws/analytics` | WebSocket | Real-time dashboard updates | All |

All endpoints accept query parameters: `start_date`, `end_date`, `instruments[]`, `playbooks[]`.

## Appendix B: Database Schema (Analytics-Specific)

### Materialized Views

**`mv_daily_pnl`** — Pre-computed daily P&L aggregation:

| Column | Type | Description |
|---|---|---|
| user_id | UUID | Foreign key to users |
| trade_date | DATE | Date of trade exit |
| net_pnl | DECIMAL(12,2) | Net P&L for the day |
| trade_count | INTEGER | Number of trades closed |
| winning_trades | INTEGER | Number of winning trades |
| losing_trades | INTEGER | Number of losing trades |
| gross_profit | DECIMAL(12,2) | Sum of winning trade P&L |
| gross_loss | DECIMAL(12,2) | Sum of losing trade P&L (absolute value) |
| total_r | DECIMAL(8,2) | Sum of R-multiples for the day |
| avg_slippage_ticks | DECIMAL(6,2) | Average slippage in ticks |

Refresh schedule: on trade close (incremental update) and nightly full refresh at 00:00 UTC.

**`mv_metrics_cache`** — Pre-computed metric values per user per filter combination:

| Column | Type | Description |
|---|---|---|
| user_id | UUID | Foreign key to users |
| filter_hash | VARCHAR(64) | SHA-256 hash of active filter state |
| metrics_json | JSONB | All computed metrics as JSON |
| computed_at | TIMESTAMPTZ | When metrics were last computed |
| trade_count | INTEGER | Number of trades in the computation |

Cache invalidation: on new trade close, on filter change (check if cached result exists).

### Indexes

```sql
CREATE INDEX idx_trades_user_exit ON trades(user_id, exit_timestamp);
CREATE INDEX idx_trades_user_instrument ON trades(user_id, instrument);
CREATE INDEX idx_trades_user_playbook ON trades(user_id, playbook_id);
CREATE INDEX idx_trades_user_exit_instrument ON trades(user_id, exit_timestamp, instrument);
CREATE INDEX idx_trades_user_exit_playbook ON trades(user_id, exit_timestamp, playbook_id);
CREATE INDEX idx_journal_entries_trade ON journal_entries(trade_id);
CREATE INDEX idx_mv_daily_pnl_user_date ON mv_daily_pnl(user_id, trade_date);
CREATE INDEX idx_mv_metrics_cache_user_hash ON mv_metrics_cache(user_id, filter_hash);
```

## Appendix C: Glossary

| Term | Definition |
|---|---|
| R-Multiple | Trade P&L divided by initial risk (stop distance x contract value). A 2R trade earned twice the amount risked. |
| MAE | Maximum Adverse Excursion — the largest unrealized loss during a trade's holding period. |
| MFE | Maximum Favorable Excursion — the largest unrealized gain during a trade's holding period. |
| Sharpe Ratio | Risk-adjusted return: (mean return - risk-free rate) / standard deviation of returns. Higher is better. |
| Sortino Ratio | Like Sharpe but uses only downside deviation, ignoring upside volatility. |
| Calmar Ratio | Annualized return divided by maximum drawdown. Higher is better. |
| Profit Factor | Gross profit divided by gross loss. Above 1.0 means profitable. |
| Expectancy | Expected value per trade: (win rate x avg winner) - (loss rate x avg loser). |
| Tiltmeter | Composite behavioral score (0-100) measuring emotional discipline. Inspired by Edgewonk. |
| RTH | Regular Trading Hours — the primary trading session for a futures contract. |
| Drawdown | Peak-to-trough decline in equity. Measured in dollars and as a percentage of peak equity. |
| Walk-Forward Analysis | Rolling window analysis that recalculates metrics on successive subsets of data to detect performance changes over time. |
| Monte Carlo Simulation | Statistical technique that resamples actual trades randomly to project the range of possible equity curve outcomes. |
| RLS | Row-Level Security — PostgreSQL feature that restricts which rows a user can access based on policies. |

---

*Document version: 1.0 | Last updated: February 11, 2026*
*This document is part of the TrendEdge PRD suite (PRD-006 of 11)*
