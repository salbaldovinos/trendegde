# PRD-004: Trade Journaling System

**TrendEdge -- AI-Powered Futures Trading Platform**
Component PRD 4 of 11

Version 1.0 | February 2026 | CONFIDENTIAL

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Data Models & Schema](#5-data-models--schema)
6. [Dependencies](#6-dependencies)
7. [Testing Requirements](#7-testing-requirements)
8. [Security Requirements](#8-security-requirements)
9. [Phase Mapping](#9-phase-mapping)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. Overview & Purpose

### 1.1 Problem Statement

Retail futures traders lose critical trade context because their execution tools, journaling tools, and analytics tools are separate systems. A trader who receives a TradingView alert, executes through TradersPost, and journals in TradeZella must manually bridge the data gap between all three. The original trendline parameters, the signal metadata, the fill quality, and the market context are never captured together in one record. This fragmentation means traders cannot answer fundamental questions like "Do my A+ trendline breaks with 4+ touches outperform 3-touch setups?" or "How much does FOMO cost me per month in lost R-multiples?"

### 1.2 Solution

TrendEdge's Trade Journaling System solves this by automatically creating a comprehensive journal entry the moment a trade fills -- zero user input required. The entry captures the complete lineage of every trade: from the trendline detection parameters, through the signal generation, to the execution fills and post-trade outcome. Traders then optionally enrich entries with discretionary context (conviction, emotions, notes, screenshots) that the automated system cannot capture. This produces a dataset that is both complete enough for rigorous quantitative analysis and rich enough for qualitative self-improvement.

### 1.3 Design Principles

- **Zero-input default.** A trader who never opens the journal still has a complete, accurate record of every trade. The system captures everything mechanical automatically.
- **Enrichment, not data entry.** Manual inputs add discretionary context (emotions, conviction, screenshots) that only the trader knows. The system never asks the trader to type in a fill price.
- **Full lineage preservation.** Every journal entry links back to its originating signal and trendline. Context is never lost between subsystems.
- **Query-first schema design.** The data model is designed around the questions traders need answered, not around the shape of incoming data.

### 1.4 Scope

This PRD covers:
- Automatic journal entry creation from trade execution events
- Manual enrichment interface (conviction, emotions, notes, screenshots, mistakes)
- Screenshot upload, storage, and annotation
- Trade search, filtering, sorting, and export
- Trade linking for scale-in/scale-out and related trades
- MAE/MFE tick-by-tick tracking and calculation

This PRD does **not** cover:
- The execution pipeline itself (see PRD-003: Trade Execution)
- Playbook definition and auto-classification rules (see PRD-005: Playbook System)
- Trendline detection and scoring (see PRD-002: Trendline Detection)
- Performance analytics dashboards and metrics (see PRD-006: Performance Analytics)
- AI-powered trade review and conversational analytics (see PRD-007: AI Features)

---

## 2. User Stories

### 2.1 Automatic Journaling

| ID | Story | Priority |
|---|---|---|
| US-J01 | As a trader, I want every trade automatically journaled the moment it fills so that I never have a gap in my trade record regardless of how busy I am. | P0 |
| US-J02 | As a trader, I want each journal entry to include the full trendline metadata (touch count, slope, grade, duration) so that I can later analyze performance by trendline quality without manual tagging. | P0 |
| US-J03 | As a trader, I want slippage calculated automatically (signal price vs. fill price) so that I can evaluate my execution quality over time. | P0 |
| US-J04 | As a trader, I want MAE and MFE tracked tick-by-tick for every trade so that I can determine if my stops are too tight or my targets too conservative. | P0 |
| US-J05 | As a trader, I want the session context (RTH vs. overnight, day of week, time of day) captured automatically so that I can analyze if I perform better during specific sessions. | P1 |
| US-J06 | As a trader, I want the margin type (day-trade vs. overnight) recorded so that I can assess capital efficiency and risk differences between margin regimes. | P1 |

### 2.2 Manual Enrichment

| ID | Story | Priority |
|---|---|---|
| US-J07 | As a trader, I want to record my pre-trade conviction level (1-5) so that I can correlate conviction with outcomes and learn to trust my best reads. | P0 |
| US-J08 | As a trader, I want to tag my emotional state before and during a trade so that I can quantify the cost of emotional trading. | P0 |
| US-J09 | As a trader, I want to upload chart screenshots and annotate them so that I have a visual record of what I saw at the time of the trade. | P1 |
| US-J10 | As a trader, I want to write free-text notes (pre-trade thesis and post-trade review) so that I can articulate my reasoning and learn from it later. | P0 |
| US-J11 | As a trader, I want a configurable rule compliance checklist tied to my playbook so that I can honestly assess whether I followed my own rules. | P1 |
| US-J12 | As a trader, I want to tag specific mistakes (moved stop, entered early, oversized, held too long, exited too early) so that I can track mistake frequency and cost. | P0 |

### 2.3 Search, Navigation, and Export

| ID | Story | Priority |
|---|---|---|
| US-J13 | As a trader, I want to search and filter my trades by instrument, date range, playbook, outcome (win/loss), and emotional tags so that I can find patterns in my trading. | P0 |
| US-J14 | As a trader, I want a table/list view of all my trades with sortable columns so that I can quickly scan my trading history. | P0 |
| US-J15 | As a trader, I want a detailed single-trade view showing all auto-captured and manually-entered data so that I can review any trade comprehensively. | P0 |
| US-J16 | As a trader, I want to edit journal entries after the trade closes (add notes, update tags) so that I can enrich my journal during my weekly review. | P0 |
| US-J17 | As a trader, I want to export my journal as CSV or PDF so that I can share it with mentors, use it for tax reporting, or back it up offline. | P1 |
| US-J18 | As a trader, I want to link related trades (scaling in/out, re-entries on the same trendline) so that I can analyze them as a cohesive position. | P1 |

### 2.4 Edge Cases

| ID | Story | Priority |
|---|---|---|
| US-J19 | As a trader, I want manual trades (not from a signal) to also be journaled so that my record is complete even when I deviate from the system. | P0 |
| US-J20 | As a trader, I want partial fills to be tracked and consolidated into a single journal entry so that my trade count reflects actual trading decisions, not fill fragmentation. | P0 |
| US-J21 | As a trader, I want journal entries for trades that hit stop loss vs. target vs. manual exit to be clearly distinguished so that I can analyze exit quality. | P0 |

---

## 3. Functional Requirements

### 3.1 Auto-Journal Creation

#### JR-FR-001: Zero-Input Journal Entry Creation on Trade Fill

The system SHALL automatically create a journal entry when a trade execution fill is confirmed. No user action is required. The journal entry is created as a background process triggered by the fill event from the execution pipeline (PRD-003).

**Trigger:** `trade.fill.confirmed` event from the execution pipeline.

**Behavior:**
- A new `JournalEntry` record is created and linked to the `Trade` record via `trade_id`.
- If the trade originated from a signal, the `Signal` record is linked via `signal_id` on the `Trade`.
- If the signal originated from the trendline engine, the `Trendline` record metadata is attached.
- The journal entry is created in `draft` status until the trade closes, at which point it transitions to `complete`.
- For partial fills, the system consolidates into a single journal entry per trading decision (grouped by `signal_id` or `manual_trade_group_id`).

**Error Handling:**
- If journal creation fails, the system retries up to 3 times with exponential backoff (1s, 4s, 16s).
- Failures are logged to the monitoring system and a Telegram alert is sent.
- The trade itself is never blocked or rolled back due to a journaling failure.

#### JR-FR-002: Trade Data Auto-Population

The system SHALL populate the following fields automatically from the execution pipeline, with zero manual input:

| Field | Source | Description |
|---|---|---|
| `entry_timestamp` | Broker fill event | Exact UTC timestamp of entry fill |
| `exit_timestamp` | Broker fill event | Exact UTC timestamp of exit fill |
| `entry_price` | Broker fill event | Actual fill price for entry |
| `exit_price` | Broker fill event | Actual fill price for exit |
| `signal_price` | Signal record | Intended entry price from signal |
| `slippage_ticks` | Calculated | `(fill_price - signal_price) / tick_size` |
| `slippage_dollars` | Calculated | `slippage_ticks * tick_value * quantity` |
| `instrument` | Signal/Trade record | Futures contract symbol (e.g., MNQ, CL) |
| `contract_month` | Signal/Trade record | Contract month/year (e.g., MAR2026) |
| `tick_size` | Contract spec lookup | Minimum price increment |
| `tick_value` | Contract spec lookup | Dollar value per tick |
| `notional_exposure` | Calculated | `price * multiplier * quantity` |
| `quantity` | Broker fill event | Number of contracts |
| `direction` | Signal record | `LONG` or `SHORT` |
| `signal_source` | Signal record | `trendline_engine`, `tradingview_webhook`, or `manual` |
| `setup_type` | Signal/Trendline record | `break` or `bounce` |
| `stop_price` | Signal record | Planned stop loss price |
| `target_price` | Signal record | Planned take profit price |
| `stop_distance_ticks` | Calculated | Distance from entry to stop in ticks |
| `target_distance_ticks` | Calculated | Distance from entry to target in ticks |
| `planned_rr` | Calculated | `target_distance / stop_distance` |
| `actual_r_multiple` | Calculated (on close) | `pnl_ticks / stop_distance_ticks` |
| `gross_pnl` | Calculated (on close) | `(exit_price - entry_price) * multiplier * quantity * direction_sign` |
| `commission` | Broker/config | Per-contract commission applied |
| `net_pnl` | Calculated (on close) | `gross_pnl - commission` |
| `exit_type` | Execution pipeline | `stop_loss`, `take_profit`, `manual`, `time_stop`, `trailing_stop` |
| `hold_duration` | Calculated (on close) | `exit_timestamp - entry_timestamp` |
| `session_type` | Time-based lookup | `rth` (Regular Trading Hours) or `overnight` |
| `day_of_week` | Derived from `entry_timestamp` | Monday through Friday |
| `time_of_day_bucket` | Derived from `entry_timestamp` | `pre_market`, `morning`, `midday`, `afternoon`, `close`, `overnight` |
| `margin_type` | Position/config | `day_trade` or `overnight` |

#### JR-FR-003: Trendline Metadata Attachment

When a trade originates from the trendline detection engine (PRD-002), the system SHALL attach the following trendline metadata to the journal entry:

| Field | Description |
|---|---|
| `trendline_id` | Foreign key to the originating `Trendline` record |
| `touch_count` | Number of confirmed touchpoints at time of signal |
| `slope_degrees` | Slope angle of the trendline in degrees |
| `trendline_duration_days` | Calendar days from first touch to signal |
| `candle_spacing_avg` | Average number of candles between consecutive touches |
| `candle_spacing_min` | Minimum candle spacing (worst spacing) |
| `trendline_grade` | Quality grade: `A+`, `A`, or `B` |
| `touch_points` | JSON array of `[timestamp, price]` for each touch |
| `break_candle_volume` | Volume of the candle that triggered the break/bounce |
| `distance_from_line_ticks` | Price distance from trendline at entry, in ticks |

This metadata is snapshotted at the time of signal generation and stored on the journal entry. It is not updated if the trendline is later recalculated, preserving the exact conditions under which the trading decision was made.

#### JR-FR-004: MAE/MFE Calculation and Tracking

The system SHALL track Maximum Adverse Excursion (MAE) and Maximum Favorable Excursion (MFE) for every open trade, computed from tick-by-tick or bar-by-bar price data.

**Definitions:**
- **MAE (Maximum Adverse Excursion):** The largest unrealized loss (in ticks and dollars) experienced during the life of the trade. For a long trade, this is the lowest price reached minus the entry price. For a short trade, this is the entry price minus the highest price reached.
- **MFE (Maximum Favorable Excursion):** The largest unrealized profit (in ticks and dollars) experienced during the life of the trade. For a long trade, this is the highest price reached minus the entry price. For a short trade, this is the entry price minus the lowest price reached.

**Calculation Method:**
1. While the trade is open, the system subscribes to real-time price updates from the broker connection.
2. On each tick (or 1-second bar if tick data is unavailable), the system computes the current unrealized P&L.
3. If the current unrealized loss exceeds the stored MAE, the MAE is updated.
4. If the current unrealized profit exceeds the stored MFE, the MFE is updated.
5. When the trade closes, the final MAE and MFE values are written to the `Trade` record.

**Stored Fields:**
- `mae_ticks` (integer): Maximum adverse excursion in ticks
- `mae_dollars` (decimal): Maximum adverse excursion in dollars (`mae_ticks * tick_value * quantity`)
- `mae_r` (decimal): MAE expressed as a fraction of planned risk (`mae_ticks / stop_distance_ticks`)
- `mae_timestamp` (timestamp): When the MAE occurred
- `mfe_ticks` (integer): Maximum favorable excursion in ticks
- `mfe_dollars` (decimal): Maximum favorable excursion in dollars
- `mfe_r` (decimal): MFE expressed as a fraction of planned risk
- `mfe_timestamp` (timestamp): When the MFE occurred

**Paper Trading Mode:**
For paper trades, MAE/MFE is calculated from simulated price feed at the same granularity as live trades.

**Fallback:**
If real-time tick data is temporarily unavailable, the system falls back to 1-minute OHLC bars. MAE is estimated from bar lows (longs) or highs (shorts). MFE is estimated from bar highs (longs) or lows (shorts). A `mae_mfe_source` field records `tick`, `1m_bar`, or `estimated` to indicate data quality.

### 3.2 Manual Enrichment

#### JR-FR-005: Pre-Trade Conviction Level

The system SHALL provide a conviction level input on the trade entry screen and the journal entry detail view.

**Specification:**
- Scale: 1 to 5 (integer)
- Labels: 1 = Low Conviction, 2 = Below Average, 3 = Average, 4 = High Conviction, 5 = Maximum Conviction
- Input method: Clickable star rating or numbered button group
- Default: Empty (not pre-filled). The system does not assume a conviction level.
- The conviction level can be set before the trade (on the signal confirmation screen) or after the trade (in the journal entry).
- Timestamp recorded: when the conviction level was set, to distinguish pre-trade vs. post-trade assessment.

#### JR-FR-006: Emotional State Tagging

The system SHALL provide an emotional state tagging interface.

**Predefined Tags:**
- `confident` -- Calm certainty in the setup
- `anxious` -- Nervousness or unease about the trade
- `fomo` -- Fear of missing out; entered despite reservations
- `revenge` -- Trading to recover a prior loss
- `patient` -- Waited for the setup; not forcing a trade
- `disciplined` -- Followed the playbook precisely
- `frustrated` -- Irritation from prior results affecting judgment
- `overconfident` -- Excessive certainty; may lead to oversizing or ignoring risk
- `bored` -- Trading for stimulation, not from setup quality
- `fatigued` -- Physical or mental tiredness affecting focus

**Specification:**
- Multiple tags can be selected per entry (stored as text array).
- Users can create custom emotional tags (up to 20 custom tags per user).
- Tags are selectable both pre-trade and post-trade.
- Each tag selection records a timestamp.
- The UI presents tags as a chip/pill selector with search-as-you-type for custom tags.

#### JR-FR-007: Free-Text Trade Notes

The system SHALL provide structured free-text note fields for each journal entry.

**Fields:**
- `pre_trade_thesis` (text, max 5,000 characters): The trader's reasoning for entering the trade, written before or at the time of entry. Supports Markdown formatting.
- `post_trade_review` (text, max 5,000 characters): The trader's retrospective analysis after the trade closes. Supports Markdown formatting.
- `general_notes` (text, max 5,000 characters): Any additional observations, market context, or personal notes.

**Behavior:**
- Auto-save on blur or after 3 seconds of inactivity (debounced).
- Version history: the system stores the last 10 edits to each note field with timestamps, allowing the trader to see how their thinking evolved.
- Notes are full-text indexed for search (see JR-FR-012).

#### JR-FR-008: Chart Screenshot Upload and Storage

The system SHALL allow traders to upload chart screenshots and attach them to journal entries.

**Specification:**
- Accepted formats: PNG, JPEG, WebP
- Maximum file size: 10 MB per image
- Maximum uploads per journal entry: 10 screenshots
- Storage backend: Supabase Storage (S3-compatible)
- File naming convention: `{user_id}/{trade_id}/{timestamp}_{original_filename}`
- Thumbnails: Generated server-side at 300px width for list views (using Pillow or Sharp)
- The upload interface supports drag-and-drop and file picker
- Upload progress indicator shown during transfer
- Each screenshot has an optional `caption` field (max 500 characters)
- Screenshots can be reordered via drag-and-drop
- Screenshots can be deleted individually

**Image Processing Pipeline:**
1. Client-side: Validate file type and size before upload
2. Upload to Supabase Storage via signed upload URL
3. Server-side: Generate thumbnail, extract EXIF metadata (strip GPS data for privacy), store metadata in database
4. Return signed download URL (expires in 1 hour, refreshed on access)

#### JR-FR-009: Screenshot Annotation Tools

The system SHALL provide client-side annotation tools for chart screenshots.

**Annotation Tools:**
- **Freehand drawing** -- Pen tool with configurable color (red, green, blue, yellow, white) and thickness (1px, 2px, 4px)
- **Straight line** -- Click-and-drag to draw lines (for marking trendlines, support/resistance)
- **Rectangle** -- Click-and-drag to draw rectangles (for highlighting zones)
- **Arrow** -- Click-and-drag to draw arrows (for indicating direction or points of interest)
- **Text label** -- Click to place text annotation (configurable font size: 12px, 16px, 24px)
- **Eraser** -- Remove individual annotations

**Specification:**
- Annotations are stored as a separate JSON overlay, not baked into the original image. The original screenshot is preserved unmodified.
- Annotation data format: Array of annotation objects, each with `type`, `coordinates`, `style`, and `timestamp`.
- The annotated view is rendered client-side by compositing the annotation layer on top of the original image.
- An "export annotated" button renders the composite to a new PNG for sharing.
- Undo/redo support (up to 50 actions).

**Implementation:** Use HTML5 Canvas or a library such as Fabric.js for the annotation layer.

#### JR-FR-010: Mistake Tagging System

The system SHALL provide a mistake tagging interface to categorize execution errors.

**Predefined Mistake Tags:**
- `moved_stop` -- Moved stop loss away from original level
- `entered_early` -- Entered before the signal confirmed
- `entered_late` -- Entered after the optimal entry window
- `oversized` -- Position size exceeded the plan
- `undersized` -- Position size was too small relative to plan
- `held_too_long` -- Did not exit at target or when thesis invalidated
- `exited_too_early` -- Took profit before target was reached
- `no_stop` -- Entered without a defined stop loss
- `averaged_down` -- Added to a losing position without plan
- `ignored_signal` -- Did not take a valid signal (omission error, tracked separately)
- `wrong_instrument` -- Traded the wrong contract or month
- `wrong_direction` -- Entered opposite to the intended direction

**Specification:**
- Multiple mistake tags can be selected per entry (stored as text array).
- Users can create custom mistake tags (up to 20 custom tags per user).
- Each mistake tag has an optional `cost_estimate` field (decimal, in dollars): the trader's estimate of how much this mistake cost them on this specific trade. This is not auto-calculated; it is the trader's subjective assessment.
- Mistake tags are only available after the trade closes (not pre-trade).
- The system tracks aggregate mistake statistics: frequency, total estimated cost, most common mistakes (surfaced in PRD-006 Performance Analytics).

#### JR-FR-011: Rule Compliance Checklist

The system SHALL provide a configurable rule compliance checklist for each journal entry, tied to the trade's assigned playbook (PRD-005).

**Specification:**
- Each playbook defines a list of compliance rules (see PRD-005 for playbook configuration).
- When a journal entry is created, the system loads the checklist from the assigned playbook.
- Each checklist item is a yes/no toggle with an optional note field (max 500 characters).
- Compliance score is calculated as `(checked_items / total_items) * 100`.

**Default Checklist (A+ Trendline Break playbook):**
1. Did the trendline have 3+ confirmed touches?
2. Was candle spacing >= 6 candles between touches?
3. Was the slope < 45 degrees?
4. Was the trendline at least 3 weeks old?
5. Did a 4H candle close past the trendline (not just wick)?
6. Was the stop placed at the safety line (4th candle)?
7. Was the target at the first S/R level at >= 2R?
8. Was position size within the risk budget (1-2% of account)?
9. Were there no conflicting open positions in correlated instruments?
10. Was this trade taken during planned trading hours?

**Behavior:**
- The checklist is presented when the trade closes or when the trader opens the journal entry for review.
- If any item is unchecked, the system prompts (but does not require) a brief explanation in the note field.
- Compliance data feeds into the behavioral analytics (PRD-006).

### 3.3 Search, Filtering, and Views

#### JR-FR-012: Trade Search and Filtering

The system SHALL provide a comprehensive search and filter interface for the trade journal.

**Filter Dimensions:**

| Filter | Type | Options |
|---|---|---|
| Date range | Date picker | Start date, end date, preset ranges (today, this week, this month, last 30 days, this quarter, YTD, custom) |
| Instrument | Multi-select dropdown | All traded instruments |
| Playbook | Multi-select dropdown | All user playbooks |
| Direction | Toggle | Long, Short, All |
| Outcome | Toggle group | Winner, Loser, Breakeven, All |
| Setup type | Toggle group | Break, Bounce, All |
| Signal source | Multi-select | Trendline Engine, TradingView Webhook, Manual |
| Trendline grade | Multi-select | A+, A, B |
| Emotional state | Multi-select chips | All predefined + custom tags |
| Mistake tags | Multi-select chips | All predefined + custom tags |
| Conviction level | Range slider | 1-5 |
| R-multiple range | Range slider | Min R to Max R |
| P&L range | Number inputs | Min $ to Max $ |
| Session type | Toggle | RTH, Overnight, All |
| Exit type | Multi-select | Stop Loss, Take Profit, Manual, Time Stop, Trailing Stop |
| Has screenshots | Toggle | Yes, No, All |
| Has notes | Toggle | Yes, No, All |

**Full-Text Search:**
- A search bar at the top of the journal view searches across: `pre_trade_thesis`, `post_trade_review`, `general_notes`, screenshot captions, and instrument names.
- Search uses PostgreSQL full-text search (`tsvector`/`tsquery`) with English language stemming.
- Search terms are highlighted in results.

**Saved Filters:**
- Users can save filter configurations as named presets (e.g., "A+ breaks in crude oil", "Revenge trades", "Losing overnight trades").
- Up to 20 saved filter presets per user.

#### JR-FR-013: Trade List/Table View

The system SHALL provide a sortable, paginated table view of journal entries.

**Default Columns:**

| Column | Sortable | Default Sort |
|---|---|---|
| Date/Time | Yes | Descending (newest first) |
| Instrument | Yes | -- |
| Direction (Long/Short) | Yes | -- |
| Setup Type | Yes | -- |
| Playbook | Yes | -- |
| Entry Price | Yes | -- |
| Exit Price | Yes | -- |
| Quantity | Yes | -- |
| Gross P&L ($) | Yes | -- |
| Net P&L ($) | Yes | -- |
| R-Multiple | Yes | -- |
| MAE (ticks) | Yes | -- |
| MFE (ticks) | Yes | -- |
| Hold Duration | Yes | -- |
| Conviction | Yes | -- |
| Compliance % | Yes | -- |
| Mistakes | No | -- |
| Screenshots | No | -- |

**Specification:**
- Pagination: 25 rows per page (configurable: 10, 25, 50, 100).
- Column visibility: Users can show/hide columns and reorder them. Preferences are persisted per user.
- Row click: Opens the trade detail view (JR-FR-014).
- Color coding: Winning trades have a subtle green left border; losing trades have a subtle red left border.
- Summary row at bottom: Total P&L, average R-multiple, win rate, number of trades for the current filtered set.
- Responsive design: On mobile, the table collapses to a card view showing instrument, direction, P&L, and date.

#### JR-FR-014: Individual Trade Detail View

The system SHALL provide a comprehensive single-trade detail view.

**Layout Sections:**

1. **Header:** Instrument, direction, date, P&L badge (green/red), R-multiple, playbook name, trendline grade badge.

2. **Execution Summary Card:**
   - Entry: timestamp, price, signal price, slippage
   - Exit: timestamp, price, exit type
   - Duration, quantity, commission
   - Gross P&L, net P&L, R-multiple

3. **Risk Analysis Card:**
   - Planned stop, target, R:R
   - Actual R-multiple
   - MAE (ticks, $, R), MFE (ticks, $, R)
   - MAE/MFE timeline visualization (a small sparkline showing unrealized P&L over the life of the trade)

4. **Trendline Context Card** (if trendline-sourced):
   - Trendline grade, touch count, slope, duration
   - Candle spacing (avg and min)
   - Embedded mini-chart showing the trendline with touch points and the trade entry/exit (rendered from stored trendline data)

5. **Session Context Card:**
   - Session type (RTH/overnight), day of week, time-of-day bucket
   - Margin type

6. **Discretionary Data Card:**
   - Conviction level (star display)
   - Emotional state tags (chip display)
   - Mistake tags (chip display with cost estimates)
   - Compliance checklist (checked/unchecked items with notes)

7. **Notes Section:**
   - Pre-trade thesis (rendered Markdown)
   - Post-trade review (rendered Markdown)
   - General notes (rendered Markdown)
   - Edit button to switch to edit mode inline

8. **Screenshots Gallery:**
   - Thumbnail grid of uploaded screenshots
   - Click to expand to full-size with annotation overlay
   - "Add Screenshot" button
   - "Annotate" button per screenshot

9. **Related Trades Section:**
   - Linked trades (scale-in/out, re-entries) with summary data
   - Link to navigate to each related trade

10. **Metadata Footer:**
    - Signal source, signal ID, trade ID
    - Created timestamp, last modified timestamp
    - "Edit" and "Export" action buttons

#### JR-FR-015: Trade Editing

The system SHALL allow traders to edit journal entries after trade completion.

**Editable Fields:**
- Conviction level
- Emotional state tags
- Mistake tags (with cost estimates)
- Pre-trade thesis, post-trade review, general notes
- Screenshots (add, remove, reorder, annotate)
- Compliance checklist
- Playbook assignment (re-classify a trade)

**Non-Editable Fields (system-generated):**
- Entry/exit timestamps and prices
- Slippage calculations
- MAE/MFE values
- R-multiple and P&L
- Signal source and trendline metadata
- Session context and contract specifications

**Behavior:**
- All edits are saved with a timestamp and stored in an `edit_history` JSON array.
- The detail view shows "Last edited: {timestamp}" if the entry has been modified.
- Bulk edit is not supported in Phase 1 to prevent accidental mass changes.

#### JR-FR-016: CSV and PDF Export

The system SHALL support exporting journal entries in CSV and PDF formats.

**CSV Export:**
- Exports all visible columns from the current filtered table view.
- One row per trade.
- All monetary values in USD.
- Timestamps in ISO 8601 format with user's timezone annotation.
- Emotional tags and mistake tags exported as semicolon-delimited strings within their respective columns.
- File name format: `trendedge_journal_{start_date}_to_{end_date}.csv`
- Maximum export: 10,000 trades per file.

**PDF Export:**
- Two modes:
  - **Summary PDF:** Table view of all trades in the current filter, with summary statistics header (total P&L, win rate, trade count, avg R-multiple).
  - **Detail PDF:** Full detail view for a single trade, including screenshots (embedded at 50% size), notes, compliance checklist.
- Branding: TrendEdge logo in header, "Generated on {date}" in footer.
- File name format: `trendedge_journal_{trade_id or date_range}.pdf`

**Implementation:** Server-side PDF generation using WeasyPrint or ReportLab. CSV generated directly from SQL query results.

#### JR-FR-017: Trade Linking (Related Trades)

The system SHALL support linking related trades together.

**Link Types:**
- `scale_in` -- Adding to an existing position
- `scale_out` -- Partially closing a position
- `re_entry` -- Re-entering after a stop-out on the same setup
- `related` -- Manually linked trades the trader considers related (e.g., same thesis in different instruments)
- `hedge` -- Opposing position in a correlated instrument

**Specification:**
- A trade can belong to one `trade_group` (for scale-in/out) and have multiple `related_trade` links.
- `trade_group` is defined by a `trade_group_id` on the `Trade` record. All trades with the same `trade_group_id` are displayed together.
- Scale-in/out: When the execution pipeline detects an order that adds to or reduces an existing position in the same instrument, it automatically assigns the same `trade_group_id`.
- Related/hedge links are created manually by the trader via a "Link Trade" action in the UI.
- Group-level metrics are calculated: total P&L, weighted average entry, total quantity, combined R-multiple.
- The trade detail view (JR-FR-014) shows all linked trades in the "Related Trades" section.

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### JR-NFR-001: Journal Entry Creation Latency

The system SHALL create the journal entry record in the database within 5 seconds of receiving the `trade.fill.confirmed` event.

**Measurement:** Time from event receipt to `journal_entries.created_at` timestamp.
**Target:** p95 < 5 seconds, p99 < 10 seconds.
**Note:** This is the database write, not the full enrichment. Trendline metadata attachment and thumbnail generation may complete asynchronously within 30 seconds.

#### JR-NFR-002: Search Response Time

The system SHALL return search and filter results within 500ms for datasets up to 10,000 trades.

**Measurement:** Server-side query execution time (database query + serialization).
**Target:** p95 < 500ms, p99 < 1,000ms.
**Indexing required:** Composite indexes on `(user_id, created_at)`, `(user_id, instrument)`, `(user_id, playbook_id)`. GIN index on `emotional_state` and `mistakes` arrays. Full-text search index on note fields.

#### JR-NFR-003: Trade Detail View Load Time

The system SHALL render the full trade detail view within 1 second, including thumbnail images.

**Measurement:** Time from navigation to fully interactive page.
**Target:** p95 < 1,000ms (excluding full-size screenshot loading, which is on-demand).

#### JR-NFR-004: MAE/MFE Update Frequency

The system SHALL update MAE/MFE values at minimum every 1 second for live trades.

**Target:** 1-second update interval during market hours when real-time data is available. 1-minute update interval when falling back to bar data.

### 4.2 Storage and Media

#### JR-NFR-005: Screenshot Upload Size and Performance

- Maximum file size per screenshot: 10 MB.
- Maximum screenshots per journal entry: 10.
- Maximum total storage per user: 5 GB (Free tier), 25 GB (Trader tier), 100 GB (Pro tier), 500 GB (Team tier).
- Upload must complete within 30 seconds on a 10 Mbps connection for a 10 MB file.
- Thumbnails (300px width) must be generated within 5 seconds of upload completion.

#### JR-NFR-006: Data Retention

- Journal entries and trade data are retained indefinitely for active subscriptions.
- Screenshots are retained for 12 months after subscription cancellation (grace period for reactivation).
- CSV/PDF exports are generated on-demand and not stored server-side (generated and streamed to the client).

### 4.3 Reliability

#### JR-NFR-007: Journal Data Integrity

- Zero tolerance for missing journal entries. Every confirmed fill MUST have a corresponding journal entry.
- A reconciliation job runs daily, comparing `trades` records to `journal_entries` records and creating any missing entries.
- All journal writes use database transactions to ensure atomicity.

#### JR-NFR-008: Annotation Data Durability

- Annotation data (JSON overlay) is stored alongside the screenshot metadata in the database, not in the file storage.
- Annotation data is included in database backups.
- Loss of annotation data is considered a data integrity incident.

### 4.4 Scalability

#### JR-NFR-009: Concurrent Users

- The system SHALL support 100 concurrent users performing journal operations (search, view, edit) without degradation.
- Phase 1 (personal system): Single user, no concurrency requirements.
- Phase 3 (multi-tenant): 100+ concurrent users.

---

## 5. Data Models & Schema

### 5.1 Core Tables

```sql
-- Trades table (owned by PRD-003, referenced here)
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    signal_id UUID REFERENCES signals(id),
    playbook_id UUID REFERENCES playbooks(id),
    trade_group_id UUID,  -- Groups scale-in/out trades

    -- Instrument
    instrument VARCHAR(20) NOT NULL,       -- e.g., 'MNQ', 'CL', 'GC'
    contract_month VARCHAR(10),            -- e.g., 'MAR2026'
    tick_size DECIMAL(10,6) NOT NULL,
    tick_value DECIMAL(10,4) NOT NULL,
    multiplier DECIMAL(10,4) NOT NULL,

    -- Execution
    direction VARCHAR(5) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(12,6),
    exit_price DECIMAL(12,6),
    signal_price DECIMAL(12,6),
    entry_timestamp TIMESTAMPTZ,
    exit_timestamp TIMESTAMPTZ,
    broker_order_ids JSONB DEFAULT '[]',   -- Array of broker order IDs
    fills JSONB DEFAULT '[]',              -- Array of fill events

    -- Slippage
    slippage_ticks DECIMAL(8,2),
    slippage_dollars DECIMAL(10,2),

    -- Risk
    stop_price DECIMAL(12,6),
    target_price DECIMAL(12,6),
    stop_distance_ticks DECIMAL(8,2),
    target_distance_ticks DECIMAL(8,2),
    planned_rr DECIMAL(6,3),
    actual_r_multiple DECIMAL(8,4),

    -- P&L
    gross_pnl DECIMAL(12,2),
    net_pnl DECIMAL(12,2),
    commission DECIMAL(8,2),

    -- MAE/MFE
    mae_ticks INTEGER,
    mae_dollars DECIMAL(10,2),
    mae_r DECIMAL(6,4),
    mae_timestamp TIMESTAMPTZ,
    mfe_ticks INTEGER,
    mfe_dollars DECIMAL(10,2),
    mfe_r DECIMAL(6,4),
    mfe_timestamp TIMESTAMPTZ,
    mae_mfe_source VARCHAR(10) DEFAULT 'tick'
        CHECK (mae_mfe_source IN ('tick', '1m_bar', 'estimated')),

    -- Context
    signal_source VARCHAR(30) NOT NULL
        CHECK (signal_source IN ('trendline_engine', 'tradingview_webhook', 'manual')),
    setup_type VARCHAR(10) CHECK (setup_type IN ('break', 'bounce')),
    exit_type VARCHAR(20)
        CHECK (exit_type IN ('stop_loss', 'take_profit', 'manual', 'time_stop', 'trailing_stop')),
    session_type VARCHAR(10) CHECK (session_type IN ('rth', 'overnight')),
    day_of_week VARCHAR(10),
    time_of_day_bucket VARCHAR(15),
    margin_type VARCHAR(15) CHECK (margin_type IN ('day_trade', 'overnight')),
    hold_duration INTERVAL,
    notional_exposure DECIMAL(14,2),

    -- Status
    status VARCHAR(15) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'closed', 'cancelled')),
    is_paper BOOLEAN NOT NULL DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Trendline snapshot (denormalized for query performance)
    trendline_id UUID REFERENCES trendlines(id),
    trendline_metadata JSONB  -- Snapshot of trendline state at signal time
);

-- Journal Entries table
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID NOT NULL UNIQUE REFERENCES trades(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),

    -- Manual enrichment
    conviction INTEGER CHECK (conviction BETWEEN 1 AND 5),
    conviction_set_at TIMESTAMPTZ,
    emotional_state TEXT[] DEFAULT '{}',
    emotional_state_timestamps JSONB DEFAULT '{}',  -- {tag: timestamp}

    -- Notes
    pre_trade_thesis TEXT,
    post_trade_review TEXT,
    general_notes TEXT,

    -- Mistakes
    mistakes TEXT[] DEFAULT '{}',
    mistake_details JSONB DEFAULT '{}',  -- {tag: {cost_estimate, note}}

    -- Compliance
    compliance_checklist JSONB DEFAULT '[]',
    -- Array of {rule: string, checked: boolean, note: string}
    compliance_score DECIMAL(5,2),  -- 0-100 percentage

    -- Edit tracking
    edit_history JSONB DEFAULT '[]',
    -- Array of {timestamp, field, old_value, new_value}

    -- Status
    status VARCHAR(10) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'complete')),

    -- Full-text search
    search_vector TSVECTOR,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Screenshots table
CREATE TABLE journal_screenshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),

    -- File info
    storage_path TEXT NOT NULL,           -- Path in Supabase Storage
    thumbnail_path TEXT,                  -- Path to generated thumbnail
    original_filename VARCHAR(255),
    file_size_bytes INTEGER NOT NULL,
    mime_type VARCHAR(50) NOT NULL,
    width INTEGER,
    height INTEGER,

    -- Metadata
    caption VARCHAR(500),
    sort_order INTEGER NOT NULL DEFAULT 0,
    annotations JSONB DEFAULT '[]',
    -- Array of {type, coordinates, style, timestamp}

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trade links table
CREATE TABLE trade_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    linked_trade_id UUID NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    link_type VARCHAR(15) NOT NULL
        CHECK (link_type IN ('scale_in', 'scale_out', 're_entry', 'related', 'hedge')),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (trade_id, linked_trade_id)
);

-- Saved filters table
CREATE TABLE journal_saved_filters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    filter_config JSONB NOT NULL,  -- Serialized filter state
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (user_id, name)
);

-- Custom tags table
CREATE TABLE user_custom_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    tag_type VARCHAR(20) NOT NULL CHECK (tag_type IN ('emotion', 'mistake')),
    tag_value VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (user_id, tag_type, tag_value)
);
```

### 5.2 Indexes

```sql
-- Trade query indexes
CREATE INDEX idx_trades_user_created ON trades(user_id, created_at DESC);
CREATE INDEX idx_trades_user_instrument ON trades(user_id, instrument);
CREATE INDEX idx_trades_user_playbook ON trades(user_id, playbook_id);
CREATE INDEX idx_trades_user_status ON trades(user_id, status);
CREATE INDEX idx_trades_trade_group ON trades(trade_group_id) WHERE trade_group_id IS NOT NULL;
CREATE INDEX idx_trades_trendline ON trades(trendline_id) WHERE trendline_id IS NOT NULL;

-- Journal query indexes
CREATE INDEX idx_journal_user_created ON journal_entries(user_id, created_at DESC);
CREATE INDEX idx_journal_trade ON journal_entries(trade_id);
CREATE INDEX idx_journal_emotions ON journal_entries USING GIN (emotional_state);
CREATE INDEX idx_journal_mistakes ON journal_entries USING GIN (mistakes);
CREATE INDEX idx_journal_search ON journal_entries USING GIN (search_vector);
CREATE INDEX idx_journal_conviction ON journal_entries(user_id, conviction)
    WHERE conviction IS NOT NULL;

-- Screenshot indexes
CREATE INDEX idx_screenshots_journal ON journal_screenshots(journal_entry_id);

-- Trade links indexes
CREATE INDEX idx_trade_links_trade ON trade_links(trade_id);
CREATE INDEX idx_trade_links_linked ON trade_links(linked_trade_id);
```

### 5.3 Row-Level Security (Phase 3)

```sql
-- Users can only access their own journal data
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
CREATE POLICY journal_user_isolation ON journal_entries
    USING (user_id = auth.uid());

ALTER TABLE journal_screenshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY screenshots_user_isolation ON journal_screenshots
    USING (user_id = auth.uid());

ALTER TABLE trade_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY trade_links_user_isolation ON trade_links
    USING (user_id = auth.uid());

ALTER TABLE journal_saved_filters ENABLE ROW LEVEL SECURITY;
CREATE POLICY saved_filters_user_isolation ON journal_saved_filters
    USING (user_id = auth.uid());

ALTER TABLE user_custom_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY custom_tags_user_isolation ON user_custom_tags
    USING (user_id = auth.uid());
```

### 5.4 Full-Text Search Trigger

```sql
-- Auto-update search vector on journal entry changes
CREATE OR REPLACE FUNCTION journal_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.pre_trade_thesis, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.post_trade_review, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.general_notes, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER journal_search_vector_trigger
    BEFORE INSERT OR UPDATE OF pre_trade_thesis, post_trade_review, general_notes
    ON journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION journal_search_vector_update();
```

---

## 6. Dependencies

### 6.1 Upstream Dependencies

| Dependency | PRD | What This System Needs | Impact if Unavailable |
|---|---|---|---|
| Trade Execution Pipeline | PRD-003 | `trade.fill.confirmed` events with full fill data, order IDs, signal reference | Journal entries cannot be auto-created. Manual entry fallback required. |
| Trendline Detection Engine | PRD-002 | Trendline metadata (touch count, slope, grade, duration, touch points) snapshotted at signal time | Journal entries are created without trendline context. Trendline-specific analytics are unavailable. |
| Playbook System | PRD-005 | Playbook ID assignment, compliance checklist definition, auto-classification rules | Trades are journaled without playbook association. Compliance checklists are empty. |
| Contract Specifications | PRD-003 | Tick size, tick value, multiplier for each instrument | Slippage, MAE/MFE, and P&L calculations are blocked. |
| Broker Real-Time Data | PRD-003 | Tick-by-tick or 1-minute price stream for open positions | MAE/MFE tracking degrades to estimated values. |

### 6.2 Downstream Consumers

| Consumer | PRD | What It Needs from Journaling |
|---|---|---|
| Performance Analytics | PRD-006 | Complete trade records with P&L, R-multiples, MAE/MFE, emotional tags, mistake tags, compliance scores |
| AI Trade Review | PRD-007 | Full journal entry data for generating personalized trade reviews and conversational queries |
| Playbook Analytics | PRD-005 | Trades grouped by playbook with outcome data for per-playbook performance metrics |

### 6.3 Infrastructure Dependencies

| Component | Technology | Purpose |
|---|---|---|
| Database | PostgreSQL 16 (Supabase) | Primary storage for all journal data |
| File Storage | Supabase Storage | Screenshot and thumbnail storage |
| Task Queue | Celery + Redis | Async journal creation, thumbnail generation, reconciliation |
| Cache | Redis (Upstash) | Search result caching, filter preset caching |
| Real-time | WebSocket (FastAPI) | Push journal updates to dashboard |

---

## 7. Testing Requirements

### 7.1 Auto-Journaling Accuracy Testing

#### JR-TEST-001: Fill-to-Journal Creation

**Objective:** Verify that every `trade.fill.confirmed` event results in a journal entry.

**Test Cases:**
- TC-001a: Single fill on a trendline engine signal creates a journal entry with all auto-populated fields within 5 seconds.
- TC-001b: Single fill on a TradingView webhook signal creates a journal entry with signal source = `tradingview_webhook`.
- TC-001c: Manual trade fill creates a journal entry with signal source = `manual`.
- TC-001d: Multiple partial fills for the same order are consolidated into a single journal entry.
- TC-001e: Simultaneous fills on two different instruments create two separate journal entries.
- TC-001f: Fill event followed by immediate journal service outage: retries succeed and entry is created within 60 seconds.
- TC-001g: Duplicate fill events (idempotency): only one journal entry is created.

#### JR-TEST-002: Data Population Accuracy

**Objective:** Verify all auto-populated fields are correctly calculated.

**Test Cases:**
- TC-002a: Slippage calculation: signal price 4500.00, fill price 4500.50, tick size 0.25 for MNQ results in slippage_ticks = 2.
- TC-002b: P&L calculation for a long MNQ trade: entry 4500.00, exit 4510.00, quantity 2, multiplier $2.00 results in gross_pnl = $40.00.
- TC-002c: P&L calculation for a short CL trade: entry 75.50, exit 74.80, quantity 1, multiplier $10.00 results in gross_pnl = $7.00.
- TC-002d: R-multiple calculation: stop distance 10 ticks, P&L = +25 ticks results in actual_r_multiple = 2.5.
- TC-002e: Session type determination: trade at 10:30 AM ET on a Tuesday is classified as `rth`.
- TC-002f: Session type determination: trade at 2:00 AM ET is classified as `overnight`.
- TC-002g: Notional exposure: MNQ at 4500.00, multiplier $2.00, quantity 3 = $27,000.00.

### 7.2 MAE/MFE Calculation Verification

#### JR-TEST-003: MAE/MFE Accuracy

**Objective:** Verify MAE/MFE tracking produces correct values.

**Test Cases:**
- TC-003a: Long trade with monotonically increasing price: MAE = 0, MFE = (max price - entry).
- TC-003b: Long trade that dips 5 ticks then rallies 20 ticks: MAE = 5 ticks, MFE = 20 ticks.
- TC-003c: Short trade that spikes 8 ticks against then drops 15 ticks in favor: MAE = 8 ticks, MFE = 15 ticks.
- TC-003d: Trade that hits both MAE and MFE multiple times: values reflect the absolute maximum excursions.
- TC-003e: MAE timestamp corresponds to the actual time of maximum adverse excursion.
- TC-003f: Fallback to 1-minute bars: MAE/MFE values are calculated from bar highs/lows and `mae_mfe_source` = `1m_bar`.
- TC-003g: MAE_R and MFE_R are correctly calculated relative to stop distance.

### 7.3 Screenshot Upload/Retrieval Testing

#### JR-TEST-004: Screenshot Lifecycle

**Objective:** Verify screenshot upload, storage, retrieval, and deletion.

**Test Cases:**
- TC-004a: Upload a 5 MB PNG: upload completes, thumbnail generated, both URLs accessible.
- TC-004b: Upload a 10 MB JPEG: upload completes (at size limit).
- TC-004c: Upload an 11 MB file: rejected with clear error message (exceeds 10 MB limit).
- TC-004d: Upload an unsupported format (GIF, BMP, TIFF): rejected with clear error listing supported formats.
- TC-004e: Upload 10 screenshots to one entry: all accepted.
- TC-004f: Upload 11th screenshot to an entry: rejected with clear error (limit 10 per entry).
- TC-004g: Delete a screenshot: file removed from storage, thumbnail removed, database record deleted.
- TC-004h: Retrieve screenshot via signed URL: URL expires after 1 hour, new URL generated on re-access.
- TC-004i: Annotation data persists across page reloads.
- TC-004j: Export annotated screenshot produces correct composite PNG.

### 7.4 Search and Filter Testing

#### JR-TEST-005: Search and Filter Correctness

**Objective:** Verify search and filter operations return correct results.

**Test Cases:**
- TC-005a: Filter by instrument "MNQ": returns only MNQ trades.
- TC-005b: Filter by date range Jan 1-31: returns only trades within that range.
- TC-005c: Filter by outcome "Winner" AND instrument "CL": returns only winning CL trades.
- TC-005d: Filter by emotional state "fomo": returns trades where `emotional_state` contains `fomo`.
- TC-005e: Filter by mistake tag "moved_stop": returns trades where `mistakes` contains `moved_stop`.
- TC-005f: Filter by conviction >= 4: returns trades with conviction 4 or 5.
- TC-005g: Filter by R-multiple range -2.0 to 3.0: returns trades within that range.
- TC-005h: Full-text search "crude oil thesis": returns entries with matching text in notes.
- TC-005i: Combined filters (3+ active): returns correct intersection of all filter criteria.
- TC-005j: Empty result set: displays "No trades match your filters" message, not an error.
- TC-005k: Search with 5,000 trades in database: response time < 500ms.

### 7.5 Export Format Validation

#### JR-TEST-006: Export Correctness

**Objective:** Verify CSV and PDF exports contain correct, well-formatted data.

**Test Cases:**
- TC-006a: CSV export of 100 trades: all columns present, values match database, file opens correctly in Excel.
- TC-006b: CSV with special characters in notes (commas, quotes, newlines): properly escaped per RFC 4180.
- TC-006c: CSV timestamps match user's configured timezone.
- TC-006d: PDF summary export: table renders correctly, summary statistics match filtered data.
- TC-006e: PDF detail export: all sections render, screenshots embedded, Markdown notes rendered as formatted text.
- TC-006f: Export of 10,000 trades (max): completes within 30 seconds.
- TC-006g: Export with active filters: only filtered trades are included, not all trades.

### 7.6 Reconciliation Testing

#### JR-TEST-007: Data Integrity

**Objective:** Verify the daily reconciliation job catches and fixes missing entries.

**Test Cases:**
- TC-007a: Create a trade without a journal entry (simulate failure): reconciliation job creates the missing entry within 24 hours.
- TC-007b: All trades have journal entries: reconciliation job completes with zero corrections.
- TC-007c: Reconciliation report is logged with counts of missing entries found and created.

---

## 8. Security Requirements

### 8.1 User Isolation

#### JR-SEC-001: Data Access Control

- All journal queries MUST include `user_id` in the WHERE clause. No API endpoint may return another user's journal data.
- In Phase 3 (multi-tenant), PostgreSQL Row-Level Security (RLS) policies enforce user isolation at the database level, providing defense-in-depth beyond application-layer checks.
- The API layer validates that the authenticated user's ID matches the `user_id` on every read, write, update, and delete operation.

#### JR-SEC-002: Screenshot Access Control

- Screenshots are stored in user-scoped paths: `{user_id}/{trade_id}/{filename}`.
- Direct URL access to screenshots is not permitted. All access goes through signed URLs generated by the API after authentication and authorization checks.
- Signed URLs expire after 1 hour and are scoped to the specific file.
- Supabase Storage bucket policies restrict access to authenticated users with matching `user_id`.

#### JR-SEC-003: API Authentication

- All journaling API endpoints require a valid authentication token (Supabase Auth JWT).
- Token validation occurs at the middleware layer before any handler executes.
- Rate limiting: 100 requests per minute per user for journal read operations, 30 requests per minute for write operations.

### 8.2 Data Protection

#### JR-SEC-004: Data at Rest

- PostgreSQL data is encrypted at rest via Supabase's managed encryption (AES-256).
- Screenshots in Supabase Storage are encrypted at rest.
- Database backups are encrypted and stored in a separate geographic region.

#### JR-SEC-005: Data in Transit

- All API communication uses TLS 1.2+ (HTTPS).
- Screenshot uploads use HTTPS with signed upload URLs.
- WebSocket connections for real-time updates use WSS (WebSocket Secure).

#### JR-SEC-006: Sensitive Data Handling

- EXIF metadata (including GPS coordinates) is stripped from uploaded screenshots during the image processing pipeline.
- Journal notes may contain sensitive trading information; they are never included in logs or error reports.
- CSV/PDF exports are generated and streamed directly to the client; they are not stored server-side.

---

## 9. Phase Mapping

### Phase 1: Auto-Journal + Basic Notes (Weeks 7-10)

**Goal:** Every trade is automatically journaled with full execution context. Basic manual enrichment is available.

| Requirement | ID | Description |
|---|---|---|
| Auto-journal creation | JR-FR-001 | Journal entry created on fill event |
| Data auto-population | JR-FR-002 | All execution fields populated automatically |
| Trendline metadata | JR-FR-003 | Trendline data attached when available |
| MAE/MFE tracking | JR-FR-004 | Tick-by-tick tracking with fallback to 1-min bars |
| Conviction level | JR-FR-005 | 1-5 scale input |
| Emotional state tags | JR-FR-006 | Predefined tags only (no custom tags yet) |
| Free-text notes | JR-FR-007 | All three note fields, no version history yet |
| Trade list view | JR-FR-013 | Basic table with sorting, no column customization |
| Trade detail view | JR-FR-014 | Full detail view, all sections |
| Trade editing | JR-FR-015 | Edit discretionary fields post-trade |
| Trade linking (auto) | JR-FR-017 | Automatic scale-in/out grouping only |

**Not included in Phase 1:**
- Screenshot upload and annotation (JR-FR-008, JR-FR-009)
- Mistake tagging (JR-FR-010)
- Rule compliance checklist (JR-FR-011)
- Advanced search and filtering (JR-FR-012)
- CSV/PDF export (JR-FR-016)
- Manual trade linking (JR-FR-017 partial)
- Custom emotional tags
- Note version history
- Saved filter presets

### Phase 2: Full Enrichment + Screenshots + Search (Weeks 9-14)

**Goal:** Complete journaling experience with all enrichment tools, screenshot support, advanced search, and export.

| Requirement | ID | Description |
|---|---|---|
| Screenshot upload | JR-FR-008 | Full upload pipeline with thumbnails |
| Screenshot annotation | JR-FR-009 | Client-side annotation tools |
| Mistake tagging | JR-FR-010 | Predefined + custom tags with cost estimates |
| Rule compliance | JR-FR-011 | Configurable checklist per playbook |
| Search and filtering | JR-FR-012 | All filter dimensions, full-text search, saved presets |
| CSV/PDF export | JR-FR-016 | Both export formats |
| Manual trade linking | JR-FR-017 | Related/hedge links, manual grouping |
| Custom tags | JR-FR-006, JR-FR-010 | User-defined emotional and mistake tags |
| Note version history | JR-FR-007 | Last 10 edits tracked |
| Column customization | JR-FR-013 | Show/hide and reorder columns |

### Phase 3: Multi-Tenant Isolation (Weeks 15-18)

**Goal:** Production-ready multi-user system with security hardening.

| Requirement | ID | Description |
|---|---|---|
| Row-Level Security | JR-SEC-001 | RLS policies on all journal tables |
| Screenshot access control | JR-SEC-002 | Signed URLs, bucket policies |
| Storage quotas | JR-NFR-005 | Tier-based storage limits enforced |
| Rate limiting | JR-SEC-003 | Per-user rate limits on API endpoints |
| Reconciliation job | JR-NFR-007 | Daily automated integrity check |
| Concurrent user support | JR-NFR-009 | 100+ concurrent users |
| EXIF stripping | JR-SEC-006 | GPS and sensitive metadata removal |

---

## 10. Acceptance Criteria

### 10.1 Phase 1 Acceptance Criteria

| # | Criterion | Verification Method |
|---|---|---|
| AC-01 | A paper trade fill via IBKR adapter results in a journal entry appearing in the trade list within 5 seconds, with all auto-populated fields correct. | Automated integration test |
| AC-02 | A trendline engine signal that triggers a paper trade produces a journal entry containing the trendline metadata (touch count, slope, grade, duration, candle spacing). | Automated integration test |
| AC-03 | A TradingView webhook signal that triggers a paper trade produces a journal entry with `signal_source = tradingview_webhook` and correct fill data. | Automated integration test |
| AC-04 | MAE and MFE values on a closed trade match independently calculated values (from recorded price history) within 1 tick tolerance. | Automated unit test with synthetic price data |
| AC-05 | Slippage is correctly calculated as `(fill_price - signal_price) / tick_size` for both long and short trades. | Automated unit test |
| AC-06 | R-multiple is correctly calculated as `pnl_ticks / stop_distance_ticks` with correct sign (positive for winners, negative for losers). | Automated unit test |
| AC-07 | The trade detail view displays all auto-populated fields in their respective sections, with correct formatting and units. | Manual UI review |
| AC-08 | A trader can set conviction level (1-5) and emotional state tags on a journal entry, and the values persist across page reloads. | Manual UI test |
| AC-09 | A trader can write pre-trade thesis and post-trade review notes with Markdown formatting, and the rendered output is correct. | Manual UI test |
| AC-10 | The trade list view displays all trades in descending date order with correct P&L color coding (green for winners, red for losers). | Manual UI review |
| AC-11 | Scale-in/out trades on the same instrument are automatically grouped under the same `trade_group_id` and displayed together in the detail view. | Automated integration test |
| AC-12 | Partial fills for a single order are consolidated into one journal entry, not multiple entries. | Automated integration test |

### 10.2 Phase 2 Acceptance Criteria

| # | Criterion | Verification Method |
|---|---|---|
| AC-13 | A 10 MB PNG screenshot uploads successfully, a thumbnail is generated, and both the original and thumbnail are retrievable via signed URL. | Automated integration test |
| AC-14 | An 11 MB file upload is rejected with a clear error message. | Automated integration test |
| AC-15 | Screenshot annotations (line, rectangle, text) are saved, persist across sessions, and render correctly on the annotated view. | Manual UI test |
| AC-16 | Exporting an annotated screenshot produces a composite PNG with annotations baked in. | Manual test |
| AC-17 | The mistake tagging interface allows selecting multiple predefined tags and entering cost estimates, which persist correctly. | Manual UI test |
| AC-18 | The compliance checklist loads the correct rules from the assigned playbook and calculates the compliance score correctly. | Automated integration test |
| AC-19 | Filtering by 3+ simultaneous criteria (e.g., instrument + date range + emotional state) returns the correct intersection of results. | Automated test with seeded data |
| AC-20 | Full-text search for a phrase in trade notes returns matching entries with the search term highlighted. | Manual UI test |
| AC-21 | CSV export of 1,000 filtered trades produces a valid CSV file with correct column headers, properly escaped values, and accurate data. | Automated test |
| AC-22 | PDF detail export for a single trade includes all sections, embedded screenshots, and rendered Markdown notes. | Manual review |
| AC-23 | Search response time is < 500ms with 5,000 trades in the database. | Automated performance test |
| AC-24 | Saved filter presets persist and reproduce the exact same filter configuration when loaded. | Automated test |

### 10.3 Phase 3 Acceptance Criteria

| # | Criterion | Verification Method |
|---|---|---|
| AC-25 | User A cannot access User B's journal entries, screenshots, or saved filters through any API endpoint. | Automated security test |
| AC-26 | RLS policies on all journal tables prevent cross-user data access even with direct SQL queries (bypassing the API). | Database-level security test |
| AC-27 | Screenshot signed URLs from User A's session cannot be used by User B to access the file. | Automated security test |
| AC-28 | Storage quota enforcement: a user on the Free tier (5 GB) receives a clear error when attempting to upload a screenshot that would exceed their quota. | Automated test |
| AC-29 | The daily reconciliation job detects a deliberately missing journal entry (trade without corresponding journal record) and creates it. | Automated integration test |
| AC-30 | 50 concurrent users performing journal search operations maintain < 500ms p95 response time. | Load test |

---

## Appendix A: API Endpoint Summary

| Method | Endpoint | Description | Phase |
|---|---|---|---|
| GET | `/api/v1/journal` | List journal entries (paginated, filtered) | 1 |
| GET | `/api/v1/journal/{id}` | Get single journal entry with full detail | 1 |
| PATCH | `/api/v1/journal/{id}` | Update journal entry (discretionary fields) | 1 |
| POST | `/api/v1/journal/{id}/screenshots` | Upload screenshot | 2 |
| DELETE | `/api/v1/journal/{id}/screenshots/{screenshot_id}` | Delete screenshot | 2 |
| PATCH | `/api/v1/journal/{id}/screenshots/{screenshot_id}` | Update screenshot (caption, annotations, order) | 2 |
| POST | `/api/v1/journal/{id}/links` | Create trade link | 2 |
| DELETE | `/api/v1/journal/{id}/links/{link_id}` | Remove trade link | 2 |
| GET | `/api/v1/journal/export/csv` | Export filtered journal as CSV | 2 |
| GET | `/api/v1/journal/export/pdf` | Export journal as PDF (summary or detail) | 2 |
| GET | `/api/v1/journal/filters` | List saved filter presets | 2 |
| POST | `/api/v1/journal/filters` | Save a filter preset | 2 |
| DELETE | `/api/v1/journal/filters/{filter_id}` | Delete a filter preset | 2 |
| POST | `/internal/journal/create` | Internal: create journal entry from fill event (not user-facing) | 1 |

## Appendix B: Event Flow Diagram

```
Trade Fill Event Flow:
=====================

[Broker API] ──fill confirmation──> [Execution Pipeline (PRD-003)]
                                           │
                                           ├──> trade.fill.confirmed event
                                           │
                                           v
                                    [Celery Worker]
                                           │
                                    ┌──────┴──────┐
                                    │             │
                                    v             v
                            [Create Trade    [Subscribe to
                             Record]          Price Feed]
                                    │             │
                                    v             │
                            [Create Journal   │
                             Entry (draft)]   │
                                    │             │
                                    v             v
                            [Attach Trendline  [Track MAE/MFE
                             Metadata]          tick-by-tick]
                                    │             │
                                    v             │
                            [Push WebSocket    │
                             update to UI]     │
                                               │
                                               v
                                    [On Trade Close]
                                           │
                                    ┌──────┴──────┐
                                    │             │
                                    v             v
                            [Finalize        [Write MAE/MFE
                             P&L, R-mult]     to Trade record]
                                    │             │
                                    v             v
                            [Update Journal   [Journal status
                             Entry]            -> complete]
                                    │
                                    v
                            [Push final update
                             to UI via WebSocket]
```

## Appendix C: Glossary

| Term | Definition |
|---|---|
| **MAE** | Maximum Adverse Excursion. The largest unrealized loss experienced during the life of a trade, measured from the entry price. |
| **MFE** | Maximum Favorable Excursion. The largest unrealized profit experienced during the life of a trade, measured from the entry price. |
| **R-Multiple** | The trade's profit or loss expressed as a multiple of the initial risk (stop distance). A trade risking 10 ticks that gains 25 ticks has an R-multiple of 2.5R. |
| **RTH** | Regular Trading Hours. For CME futures, typically 9:30 AM - 4:00 PM ET for equity index products. |
| **Slippage** | The difference between the intended signal price and the actual fill price, measured in ticks. |
| **Safety Line** | In the Tori Trades methodology, an opposing trendline projected forward by 4 candles, used as the stop loss level. |
| **Tick** | The minimum price increment for a futures contract (e.g., 0.25 for MNQ, 0.01 for CL). |
| **Tick Value** | The dollar value of one tick of price movement per contract (e.g., $0.50 for MNQ, $10.00 for CL). |
| **Trade Group** | A collection of related trades (scale-in, scale-out) that represent a single trading decision or position. |
| **Compliance Score** | Percentage of playbook rules the trader followed on a given trade, calculated from the rule compliance checklist. |
