# PRD-005: Playbook System

**TrendEdge -- AI-Powered Futures Trading Platform**
Product Requirements Document

| Field | Value |
|---|---|
| PRD Number | PRD-005 |
| Title | Playbook System |
| Version | 1.0 |
| Date | February 2026 |
| Status | Draft |
| Author | TrendEdge Product Team |
| Classification | CONFIDENTIAL |

---

## Table of Contents

1. [Overview and Purpose](#1-overview-and-purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Data Model](#5-data-model)
6. [API Specification](#6-api-specification)
7. [Dependencies](#7-dependencies)
8. [Testing Requirements](#8-testing-requirements)
9. [Security](#9-security)
10. [Phase Mapping](#10-phase-mapping)
11. [Acceptance Criteria](#11-acceptance-criteria)

---

## 1. Overview and Purpose

### 1.1 Problem Statement

Traders who execute multiple strategy variations (e.g., 3-touch A+ trendline breaks vs. 2-touch standard breaks vs. trendline bounces) have no way to isolate which strategies actually produce positive expectancy and which erode their edge. Without independent performance tracking per setup type, traders cannot answer critical questions such as "Should I stop trading 2-touch breaks?" or "Are my bounce trades profitable enough to justify the risk?"

Most journaling tools offer basic tagging but require manual classification for every trade. This introduces inconsistency (traders miscategorize trades under stress), incompleteness (classification is skipped), and analytical blind spots (metrics are only as good as the data entered).

### 1.2 Solution

The Playbook System provides named strategy containers with independent performance tracking. Every trade is assigned to exactly one playbook, either automatically via rule-based classification using trendline engine metadata (PRD-002), or manually by the trader. Each playbook maintains its own equity curve, win rate, R-multiple statistics, and risk-adjusted return metrics, enabling rigorous per-strategy analysis.

The system is inspired by TradeZella's playbook model but fundamentally enhanced by:

- **Automated classification** from the trendline detection engine's metadata (touch count, slope, spacing, grade), eliminating manual tagging for trendline-based setups.
- **Rule compliance tracking** that measures how consistently a trader follows each playbook's defined criteria.
- **Playbook-specific risk parameters** that can override global settings (e.g., smaller position sizes for lower-conviction playbooks).
- **Playbook comparison views** for data-driven strategy allocation decisions.

### 1.3 Scope

This PRD covers the complete playbook lifecycle: creation, configuration, auto-classification rules, trade assignment, metrics calculation, comparison views, templates, sharing, and archiving. It does not cover the underlying trendline detection logic (PRD-002), trade execution mechanics (PRD-003), journal entry creation (PRD-004), or aggregate cross-playbook analytics (PRD-006).

### 1.4 Tier Limits

| Feature | Free | Trader ($49/mo) | Pro ($99/mo) | Team ($199/mo) |
|---|---|---|---|---|
| Default playbooks | 1 (A+ Trendline Break) | All 3 defaults | All 3 defaults | All 3 defaults |
| Custom playbooks | 0 | 5 | Unlimited | Unlimited |
| Auto-classification | Yes (default only) | Yes | Yes | Yes |
| Playbook templates | No | No | Yes (use) | Yes (create + share) |
| Playbook sharing | No | No | No | Yes (within team) |
| Playbook comparison | No | Side-by-side (2) | Multi-playbook | Multi-playbook + export |
| Total playbook cap | 1 | 8 | 50 | 50 per member |

---

## 2. User Stories

### 2.1 Core User Stories

| ID | Role | Story | Priority |
|---|---|---|---|
| PB-US-001 | Trendline Trader | As a trendline trader, I want my trades automatically classified into the correct playbook based on trendline metadata so that I never have to manually tag trades from the detection engine. | P0 |
| PB-US-002 | Trendline Trader | As a trendline trader, I want to see independent win rate, expectancy, and equity curve for each playbook so that I can identify which setup types are profitable and which are not. | P0 |
| PB-US-003 | Trendline Trader | As a trendline trader, I want to compare A+ trendline breaks vs. standard breaks side-by-side so that I can decide whether to stop trading 2-touch setups. | P0 |
| PB-US-004 | Discretionary Trader | As a discretionary trader, I want to create custom playbooks with my own criteria definitions so that I can track non-trendline strategies. | P0 |
| PB-US-005 | Discretionary Trader | As a discretionary trader, I want to manually assign or reassign trades to playbooks so that I can correct misclassifications or categorize manual trades. | P0 |
| PB-US-006 | Trendline Trader | As a trendline trader, I want to see a rule compliance score per playbook that tracks whether my entries matched the playbook's defined criteria so that I can measure my discipline. | P1 |
| PB-US-007 | Pro Trader | As a Pro trader, I want to set playbook-specific risk parameters (smaller size for experimental setups) so that I can limit exposure to unproven strategies. | P1 |
| PB-US-008 | Pro Trader | As a Pro trader, I want to browse and use playbook templates so that I can quickly adopt proven strategies. | P2 |
| PB-US-009 | Team Lead | As a team lead, I want to share playbooks with my team members so that everyone uses consistent strategy definitions. | P2 |
| PB-US-010 | Team Lead | As a team lead, I want to see aggregated playbook performance across all team members so that I can identify which strategies work for the team. | P2 |
| PB-US-011 | Any Trader | As a trader, I want to archive a playbook I no longer use while preserving all historical data so that my overall analytics remain accurate. | P1 |
| PB-US-012 | Any Trader | As a trader, I want trades that do not match any auto-classification rule to land in a "Custom / Manual" fallback playbook so that no trade is ever untagged. | P0 |
| PB-US-013 | Any Trader | As a trader, I want to see my playbook equity curves overlaid on a single chart so that I can visually compare strategy performance over time. | P1 |

### 2.2 Anti-Stories (Explicitly Out of Scope)

| ID | Description | Reason |
|---|---|---|
| PB-AS-001 | The system does NOT automatically disable a playbook based on poor performance. | Traders must retain full control over strategy allocation decisions. The system provides data, not mandates. |
| PB-AS-002 | The system does NOT support cross-user playbook discovery or a public marketplace in Phase 1-3. | Marketplace features are Phase 4. Templates are shared within teams only. |
| PB-AS-003 | The system does NOT create or modify trades. | Trade creation is PRD-003 (Execution) and PRD-004 (Journaling). Playbook only classifies and tracks. |

---

## 3. Functional Requirements

### 3.1 Default Playbook Seeding

**PB-FR-001**: The system SHALL seed three default playbooks for every new user account upon registration:

| Playbook Name | ID Slug | Auto-Classification | Editable | Deletable |
|---|---|---|---|---|
| A+ Trendline Break | `aplus-trendline-break` | Yes | Criteria: No. Name: No. Risk params: Yes. | No (archivable) |
| Standard Trendline Break | `standard-trendline-break` | Yes | Criteria: No. Name: No. Risk params: Yes. | No (archivable) |
| Trendline Bounce | `trendline-bounce` | Yes | Criteria: No. Name: No. Risk params: Yes. | No (archivable) |

**PB-FR-002**: The system SHALL seed a "Custom / Manual" fallback playbook for every user. This playbook:
- Cannot be deleted or archived.
- Serves as the catch-all for trades not matching any auto-classification rule.
- Is always available regardless of tier.

**PB-FR-003**: Default playbook auto-classification rules SHALL be pre-configured and immutable. Users cannot modify the classification criteria for default playbooks. They may only adjust risk parameter overrides.

**PB-FR-004**: On Free tier, only the "A+ Trendline Break" default playbook and the "Custom / Manual" fallback SHALL be active. The remaining defaults SHALL be visible but locked with an upgrade prompt.

### 3.2 Custom Playbook CRUD

**PB-FR-005**: Users on Trader tier and above SHALL be able to create custom playbooks with the following fields:

| Field | Type | Required | Constraints |
|---|---|---|---|
| `name` | string | Yes | 1-100 characters, unique per user |
| `description` | text | No | Max 2,000 characters |
| `criteria_description` | text | Yes | Max 5,000 characters. Human-readable setup rules. |
| `auto_classify_rules` | JSON | No | Valid rule schema (see PB-FR-015). Null = manual-only. |
| `color` | hex string | No | Default assigned from palette. Used in charts. |
| `icon` | string | No | From predefined icon set (20 options). |
| `risk_overrides` | JSON | No | See PB-FR-035 for schema. |
| `tags` | string[] | No | Max 10 tags, each max 30 characters. |

**PB-FR-006**: Users SHALL be able to read (list and view) all their playbooks, including:
- Active playbooks with current metrics summary.
- Archived playbooks with a visual indicator.
- Default vs. custom distinction.
- Trade count per playbook.

**PB-FR-007**: Users SHALL be able to update custom playbooks. Changes to `auto_classify_rules` do NOT retroactively reclassify existing trades. A confirmation dialog SHALL warn the user of this behavior.

**PB-FR-008**: Users SHALL be able to delete custom playbooks only if they contain zero trades. If the playbook has trades, the user must either:
- Reassign all trades to another playbook first, OR
- Archive the playbook instead (soft delete).

**PB-FR-009**: The system SHALL enforce tier-based playbook limits:
- When a user attempts to create a playbook beyond their tier limit, the system SHALL return HTTP 403 with a descriptive error message and upgrade prompt.
- Archived playbooks do NOT count toward the active limit.
- Default playbooks do NOT count toward the custom playbook limit.

**PB-FR-010**: Playbook names SHALL be unique per user (case-insensitive). The system SHALL return a validation error if a duplicate name is attempted.

### 3.3 Playbook Archiving

**PB-FR-011**: Archiving a playbook SHALL:
- Set `archived_at` timestamp and `status = 'archived'`.
- Remove the playbook from the active playbook list and comparison views by default.
- Preserve all historical trades and metrics data.
- Stop auto-classification of new trades into the archived playbook.
- NOT delete any data.

**PB-FR-012**: Archived playbooks SHALL remain queryable:
- Users can view the archived playbook's full metrics and trade history.
- Archived playbook data SHALL continue to contribute to overall (cross-playbook) analytics in PRD-006.
- A toggle in the analytics UI SHALL allow users to include/exclude archived playbooks from aggregate views.

**PB-FR-013**: Users SHALL be able to unarchive a playbook, restoring it to active status, provided the unarchival does not exceed their tier's active playbook limit.

**PB-FR-014**: Default playbooks (A+ Trendline Break, Standard Trendline Break, Trendline Bounce) may be archived but never permanently deleted. The "Custom / Manual" fallback may not be archived.

### 3.4 Auto-Classification Rules Engine

**PB-FR-015**: Auto-classification rules SHALL be defined as a JSON object conforming to the following schema:

```json
{
  "version": "1.0",
  "match_mode": "all",  // "all" (AND) or "any" (OR)
  "conditions": [
    {
      "field": "<trendline_metadata_field>",
      "operator": "<comparison_operator>",
      "value": "<threshold_value>"
    }
  ]
}
```

Supported fields (sourced from PRD-002 trendline engine metadata):

| Field | Type | Description |
|---|---|---|
| `touch_count` | integer | Number of confirmed touches on the trendline |
| `slope_angle` | float | Absolute slope angle in degrees (0-90) |
| `candle_spacing_min` | integer | Minimum candles between any two consecutive touches |
| `trendline_duration_weeks` | float | Duration from first touch to signal in weeks |
| `trendline_grade` | enum | `"A+"`, `"A"`, `"B"`, `"C"` from trendline engine |
| `setup_type` | enum | `"break"`, `"bounce"` |
| `direction` | enum | `"long"`, `"short"` |
| `instrument` | string | Futures symbol (e.g., `"CL"`, `"GC"`, `"PL"`) |
| `signal_source` | enum | `"trendline_engine"`, `"tradingview_webhook"`, `"manual"` |
| `session` | enum | `"rth"`, `"overnight"` |
| `timeframe` | enum | `"1H"`, `"4H"`, `"D"`, `"W"` |

Supported operators:

| Operator | Description | Applicable Types |
|---|---|---|
| `eq` | Equal to | All |
| `neq` | Not equal to | All |
| `gt` | Greater than | integer, float |
| `gte` | Greater than or equal | integer, float |
| `lt` | Less than | integer, float |
| `lte` | Less than or equal | integer, float |
| `in` | Value in list | enum, string |
| `not_in` | Value not in list | enum, string |

**PB-FR-016**: Default playbook auto-classification rules SHALL be:

**A+ Trendline Break:**
```json
{
  "version": "1.0",
  "match_mode": "all",
  "conditions": [
    { "field": "touch_count", "operator": "gte", "value": 3 },
    { "field": "slope_angle", "operator": "lt", "value": 45 },
    { "field": "candle_spacing_min", "operator": "gte", "value": 6 },
    { "field": "trendline_duration_weeks", "operator": "gte", "value": 3 },
    { "field": "setup_type", "operator": "eq", "value": "break" }
  ]
}
```

**Standard Trendline Break:**
```json
{
  "version": "1.0",
  "match_mode": "all",
  "conditions": [
    { "field": "touch_count", "operator": "eq", "value": 2 },
    { "field": "setup_type", "operator": "eq", "value": "break" }
  ]
}
```

**Trendline Bounce:**
```json
{
  "version": "1.0",
  "match_mode": "all",
  "conditions": [
    { "field": "touch_count", "operator": "gte", "value": 2 },
    { "field": "setup_type", "operator": "eq", "value": "bounce" }
  ]
}
```

**PB-FR-017**: The classification engine SHALL evaluate rules in priority order:
1. User-defined custom playbook rules (ordered by `priority` field, lowest number first).
2. Default playbook rules in fixed order: A+ Trendline Break, Standard Trendline Break, Trendline Bounce.
3. Fallback to "Custom / Manual" if no rules match.

**PB-FR-018**: A trade SHALL be assigned to the FIRST matching playbook only. The system uses first-match-wins semantics. There is no multi-playbook assignment.

**PB-FR-019**: Custom playbook rules SHALL include a user-configurable `priority` field (integer, 1-100). Lower values are evaluated first. Default playbooks have fixed implicit priorities of 200, 300, and 400 respectively. The "Custom / Manual" fallback has priority 9999.

**PB-FR-020**: The system SHALL validate auto-classification rules on save:
- All referenced fields must be in the supported fields list.
- All operators must be valid for the field type.
- Values must be of the correct type.
- At least one condition must be present.
- The `version` field must match a supported schema version.

**PB-FR-021**: When a trade is created (via execution pipeline PRD-003 or manual journal entry PRD-004), the classification engine SHALL:
1. Extract trendline metadata from the trade's associated signal/trendline.
2. Evaluate all active (non-archived) playbook rules in priority order.
3. Assign the trade to the first matching playbook.
4. Record the classification result: `playbook_id`, `classification_method` (`"auto"` or `"manual"`), `matched_rule_snapshot` (frozen copy of the rule at classification time).
5. If the trade has no trendline metadata (manual trade, non-trendline webhook), skip auto-classification and assign to "Custom / Manual".

**PB-FR-022**: The system SHALL provide a "test classification" endpoint that accepts a mock trade metadata payload and returns which playbook would be matched, including the matched rule details, without creating any records. This supports rule authoring and debugging.

### 3.5 Manual Trade-to-Playbook Assignment

**PB-FR-023**: Users SHALL be able to manually assign a trade to any active playbook, regardless of auto-classification results. Manual assignment sets `classification_method = "manual"` and overrides any prior auto-classification.

**PB-FR-024**: The system SHALL present a playbook selection dropdown during manual trade entry (PRD-004 journal). The dropdown:
- Shows all active playbooks ordered by most recently used.
- Pre-selects the auto-classified playbook if applicable.
- Defaults to "Custom / Manual" if no auto-classification was performed.

### 3.6 Trade Re-Classification

**PB-FR-025**: Users SHALL be able to move a trade from one playbook to another at any time. Re-classification SHALL:
- Update the trade's `playbook_id`.
- Set `classification_method = "manual"` and record `reclassified_at` timestamp.
- Preserve the original classification in an audit trail (`original_playbook_id`, `original_classification_method`).
- Trigger metrics recalculation for both the source and destination playbooks.

**PB-FR-026**: Bulk re-classification SHALL be supported: users can select multiple trades and move them to a target playbook in a single operation. The system SHALL process up to 500 trades per bulk operation.

**PB-FR-027**: Re-classification to an archived playbook SHALL NOT be permitted. The user must first unarchive the target playbook.

### 3.7 Per-Playbook Metrics Calculation

**PB-FR-028**: Each playbook SHALL independently calculate and display the following metrics based solely on trades assigned to that playbook:

**Core Performance Metrics:**

| Metric | ID | Formula | Min Trades |
|---|---|---|---|
| Win Rate | `win_rate` | `winning_trades / total_closed_trades` | 1 |
| Average R-Multiple | `avg_r_multiple` | `sum(r_multiples) / total_closed_trades` | 1 |
| Profit Factor | `profit_factor` | `sum(winning_pnl) / abs(sum(losing_pnl))` | 1 win + 1 loss |
| Expectancy | `expectancy` | `(win_rate * avg_win) - (loss_rate * avg_loss)` | 1 win + 1 loss |
| Expectancy (R) | `expectancy_r` | `(win_rate * avg_win_r) - (loss_rate * avg_loss_r)` | 1 win + 1 loss |
| Average Winner | `avg_winner` | `sum(winning_pnl) / winning_trades` | 1 win |
| Average Loser | `avg_loser` | `sum(losing_pnl) / losing_trades` | 1 loss |
| Largest Win | `largest_win` | `max(pnl) where pnl > 0` | 1 win |
| Largest Loss | `largest_loss` | `min(pnl) where pnl < 0` | 1 loss |
| Total P&L | `total_pnl` | `sum(pnl)` | 1 |
| Total R | `total_r` | `sum(r_multiples)` | 1 |

**Risk-Adjusted Metrics:**

| Metric | ID | Formula | Min Trades |
|---|---|---|---|
| Sharpe Ratio | `sharpe_ratio` | `mean(returns) / std(returns) * sqrt(252)` | 10 |
| Sortino Ratio | `sortino_ratio` | `mean(returns) / downside_std(returns) * sqrt(252)` | 10 |
| Max Drawdown ($) | `max_drawdown_dollar` | Maximum peak-to-trough decline in equity | 2 |
| Max Drawdown (%) | `max_drawdown_pct` | Maximum peak-to-trough percentage decline | 2 |

**Behavioral Metrics:**

| Metric | ID | Formula | Min Trades |
|---|---|---|---|
| Average Hold Time | `avg_hold_time` | `avg(exit_time - entry_time)` | 1 |
| Max Consecutive Wins | `max_consec_wins` | Longest streak of consecutive wins | 1 |
| Max Consecutive Losses | `max_consec_losses` | Longest streak of consecutive losses | 1 |
| Trade Count | `trade_count` | Total trades (open + closed) | 0 |
| Closed Trade Count | `closed_trade_count` | Trades with exit | 0 |

**PB-FR-029**: Each playbook SHALL maintain an independent equity curve:
- The equity curve tracks cumulative P&L over time for trades in that playbook only.
- Data points are generated at each trade close timestamp.
- The curve starts at 0 (relative P&L, not absolute account equity).
- Both dollar-denominated and R-multiple-denominated curves SHALL be available.

**PB-FR-030**: Metrics SHALL be recalculated when any of the following events occur:
- A trade assigned to the playbook is closed (exit recorded).
- A trade is reclassified into or out of the playbook (PB-FR-025).
- A trade's P&L is corrected or updated (fill adjustment, commission update).

**PB-FR-031**: Metrics requiring a minimum trade count (see "Min Trades" column in PB-FR-028) SHALL display "Insufficient data" with the current count and required count when the threshold is not met.

**PB-FR-032**: Metrics SHALL support date-range filtering. Users can view playbook metrics for:
- All time (default).
- Last 30, 90, 180 days.
- Year-to-date.
- Custom date range.
- Rolling window (e.g., last N trades).

### 3.8 Playbook Comparison View

**PB-FR-033**: The system SHALL provide a side-by-side comparison view showing metrics for 2 or more selected playbooks in a table format:
- Rows: metric names.
- Columns: selected playbooks.
- Best-performing value per row highlighted in green.
- Worst-performing value per row highlighted in red.
- Date-range filter applied uniformly across all compared playbooks.

**PB-FR-034**: The comparison view SHALL include:
- Overlaid equity curves (all selected playbooks on one chart, color-coded).
- R-multiple distribution histograms per playbook.
- Win rate trend over time (rolling 20-trade window) per playbook.
- Statistical significance indicator when comparing two playbooks (chi-squared test for win rate difference, minimum 30 trades each).

### 3.9 Playbook-Specific Risk Parameters

**PB-FR-035**: Each playbook SHALL support optional risk parameter overrides stored in `risk_overrides` JSON:

```json
{
  "max_position_size": null,       // contracts, null = use global
  "max_risk_per_trade_pct": null,  // % of account, null = use global
  "max_risk_per_trade_dollar": null, // $, null = use global
  "max_concurrent_positions": null, // count, null = use global
  "min_rr_ratio": null,            // minimum R:R, null = use global
  "max_daily_loss_dollar": null,   // $ daily stop for this playbook only
  "max_weekly_trades": null        // rate limit per playbook
}
```

**PB-FR-036**: When a trade signal matches a playbook with risk overrides, the execution pipeline (PRD-003) SHALL use the playbook's overrides instead of the user's global risk settings for any non-null fields.

**PB-FR-037**: Risk overrides SHALL be validated to ensure they are more restrictive than or equal to global settings. The system SHALL warn (not block) if a playbook override is less restrictive than the global setting.

### 3.10 Rule Compliance Tracking

**PB-FR-038**: Each playbook SHALL define an optional compliance checklist: a list of criteria statements that a trade should meet to be considered "compliant" with the playbook's rules.

Example checklist for "A+ Trendline Break":
```json
{
  "checklist": [
    { "id": "c1", "label": "Waited for 4H candle close past trendline", "auto_check": true, "field": "setup_type", "value": "break" },
    { "id": "c2", "label": "Stop placed at safety line (4th candle)", "auto_check": false },
    { "id": "c3", "label": "Target at first S/R >= 2R", "auto_check": true, "field": "planned_rr", "operator": "gte", "value": 2.0 },
    { "id": "c4", "label": "Position size within risk limits", "auto_check": true, "field": "risk_pct", "operator": "lte", "value_ref": "max_risk_per_trade_pct" },
    { "id": "c5", "label": "No active correlated positions", "auto_check": false }
  ]
}
```

**PB-FR-039**: For each trade, the compliance score SHALL be calculated as:
- `compliance_score = checked_items / total_items * 100`
- Items with `auto_check: true` are evaluated automatically from trade metadata.
- Items with `auto_check: false` are presented to the user in the journal entry (PRD-004) for manual check/uncheck.

**PB-FR-040**: The system SHALL track a rolling compliance rate per playbook:
- `playbook_compliance_rate = avg(trade_compliance_scores)` over the date range.
- Displayed on the playbook detail page and in comparison views.

**PB-FR-041**: The system SHALL correlate compliance score with trade outcome:
- Show average P&L and R-multiple for high-compliance trades (>= 80%) vs. low-compliance trades (< 80%) within each playbook.
- This enables traders to quantify the cost of breaking their own rules.

### 3.11 Playbook Templates

**PB-FR-042**: Pro and Team tier users SHALL be able to save a custom playbook as a template. A template captures:
- `name`, `description`, `criteria_description`.
- `auto_classify_rules` (if any).
- `compliance_checklist` (if any).
- `risk_overrides` (if any).
- Template does NOT include historical trade data or metrics.

**PB-FR-043**: Pro users SHALL be able to instantiate a playbook from a template. This creates a new playbook pre-populated with the template's configuration, which the user can then modify.

**PB-FR-044**: Team tier users SHALL be able to share templates with other members of their team (organization). Shared templates appear in a "Team Templates" section in the playbook creation flow.

**PB-FR-045**: Template metadata SHALL include:
- `created_by` (user ID, shown as display name).
- `created_at` timestamp.
- `usage_count` (how many playbooks have been created from this template).
- `version` (incremented on template update).

### 3.12 Playbook Sharing (Team Tier)

**PB-FR-046**: Team tier organizations SHALL support playbook sharing with two permission levels:
- **View**: Team member can see the shared playbook's configuration and metrics across all team members' trades tagged to that playbook definition.
- **Use**: Team member can classify their own trades into the shared playbook. Their trades are tracked under the shared playbook's metrics but also visible in their personal analytics.

**PB-FR-047**: Shared playbook metrics SHALL support two views:
- **Individual**: Metrics for the viewing user's trades only.
- **Team aggregate**: Combined metrics across all team members' trades in the shared playbook.
- **Member breakdown**: Per-member metrics within the shared playbook.

**PB-FR-048**: Only team admins (role: `admin` or `owner`) SHALL be able to create shared playbooks and manage sharing permissions. Team members with role `member` can use shared playbooks but not create or modify them.

**PB-FR-049**: When a team member leaves an organization, their trades remain tagged to the shared playbook for historical accuracy, but they lose access to team aggregate views. Their individual playbook copy becomes a personal (unshared) playbook.

---

## 4. Non-Functional Requirements

### 4.1 Performance

**PB-NFR-001**: Auto-classification SHALL complete within 2 seconds of trade creation. This includes rule evaluation against all active playbooks and the database write of the classification result. Measured at p95 latency.

**PB-NFR-002**: Metrics recalculation SHALL complete within 5 seconds of the triggering event (trade close, reclassification, or update). For playbooks with fewer than 1,000 trades, target is under 1 second. Measured at p95 latency.

**PB-NFR-003**: The playbook list API SHALL respond within 200ms for users with up to 50 active playbooks. Measured at p95 latency.

**PB-NFR-004**: The comparison view SHALL render within 3 seconds for up to 5 playbooks with up to 1,000 trades each. Measured at p95 latency.

**PB-NFR-005**: Bulk reclassification of 500 trades SHALL complete within 30 seconds, including metrics recalculation for affected playbooks.

### 4.2 Scalability

**PB-NFR-006**: The system SHALL support up to 50 playbooks per user (across active and custom, excluding archived).

**PB-NFR-007**: Each playbook SHALL support up to 10,000 trades without degradation of metrics calculation performance.

**PB-NFR-008**: The auto-classification rules engine SHALL evaluate up to 50 rule sets per trade classification without exceeding the 2-second latency requirement (PB-NFR-001).

### 4.3 Data Integrity

**PB-NFR-009**: Every closed trade SHALL be assigned to exactly one playbook at all times. The system SHALL never allow a trade to exist without a playbook assignment.

**PB-NFR-010**: Metrics recalculation SHALL be idempotent: running the calculation multiple times for the same playbook state SHALL produce identical results.

**PB-NFR-011**: The classification audit trail (original playbook, reclassification history) SHALL be immutable. Historical classification records cannot be deleted.

### 4.4 Availability

**PB-NFR-012**: Auto-classification SHALL function independently of the trendline detection engine's availability. If trendline metadata is unavailable, trades SHALL be assigned to "Custom / Manual" with a system note indicating metadata was missing.

**PB-NFR-013**: Metrics SHALL be served from pre-computed/cached values with a cache invalidation strategy, not calculated on every request.

### 4.5 Usability

**PB-NFR-014**: The playbook creation form SHALL be completable in under 60 seconds for a user with a clear strategy definition. Only `name` and `criteria_description` are required fields.

**PB-NFR-015**: Auto-classification rules SHALL provide a visual rule builder (UI) in addition to raw JSON editing. The visual builder SHALL generate valid JSON and vice versa.

---

## 5. Data Model

### 5.1 Database Schema (PostgreSQL / Supabase)

```sql
-- Playbook definition
CREATE TABLE playbooks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    org_id          UUID REFERENCES organizations(id),  -- Team tier only
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(120) NOT NULL,
    description     TEXT,
    criteria_description TEXT NOT NULL,
    auto_classify_rules JSONB,          -- Rule engine JSON (PB-FR-015 schema)
    risk_overrides  JSONB,              -- Risk parameter overrides (PB-FR-035)
    compliance_checklist JSONB,         -- Compliance items (PB-FR-038)
    color           VARCHAR(7) DEFAULT '#6366F1',
    icon            VARCHAR(50) DEFAULT 'chart-line',
    tags            TEXT[] DEFAULT '{}',
    priority        INTEGER DEFAULT 50, -- Auto-classification priority (1-100)
    is_default      BOOLEAN DEFAULT FALSE,
    is_shared       BOOLEAN DEFAULT FALSE,
    share_permission VARCHAR(10) DEFAULT 'view', -- 'view' | 'use'
    status          VARCHAR(20) DEFAULT 'active', -- 'active' | 'archived'
    archived_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_playbook_name_per_user UNIQUE (user_id, name),
    CONSTRAINT unique_playbook_slug_per_user UNIQUE (user_id, slug),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 9999),
    CONSTRAINT valid_status CHECK (status IN ('active', 'archived'))
);

-- Index for classification engine priority ordering
CREATE INDEX idx_playbooks_classification
    ON playbooks (user_id, status, priority)
    WHERE status = 'active' AND auto_classify_rules IS NOT NULL;

-- Trade-to-playbook assignment
-- (trade_id references trades table from PRD-003)
CREATE TABLE trade_playbook_assignments (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id                    UUID NOT NULL REFERENCES trades(id),
    playbook_id                 UUID NOT NULL REFERENCES playbooks(id),
    classification_method       VARCHAR(10) NOT NULL, -- 'auto' | 'manual'
    matched_rule_snapshot       JSONB,  -- Frozen copy of matched rule at classification time
    original_playbook_id        UUID REFERENCES playbooks(id),
    original_classification_method VARCHAR(10),
    reclassified_at             TIMESTAMPTZ,
    compliance_checks           JSONB,  -- { "c1": true, "c2": false, ... }
    compliance_score            DECIMAL(5,2),
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_trade_assignment UNIQUE (trade_id)
);

CREATE INDEX idx_tpa_playbook ON trade_playbook_assignments (playbook_id);
CREATE INDEX idx_tpa_trade ON trade_playbook_assignments (trade_id);

-- Pre-computed playbook metrics (refreshed on trade events)
CREATE TABLE playbook_metrics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playbook_id         UUID NOT NULL REFERENCES playbooks(id),
    period_type         VARCHAR(20) NOT NULL, -- 'all_time' | 'ytd' | '30d' | '90d' | '180d'
    period_start        DATE,
    period_end          DATE,

    -- Core metrics
    trade_count         INTEGER DEFAULT 0,
    closed_trade_count  INTEGER DEFAULT 0,
    winning_trades      INTEGER DEFAULT 0,
    losing_trades       INTEGER DEFAULT 0,
    breakeven_trades    INTEGER DEFAULT 0,
    win_rate            DECIMAL(5,4),
    avg_r_multiple      DECIMAL(8,4),
    total_r             DECIMAL(10,4),
    profit_factor       DECIMAL(8,4),
    expectancy          DECIMAL(12,2),
    expectancy_r        DECIMAL(8,4),
    avg_winner          DECIMAL(12,2),
    avg_loser           DECIMAL(12,2),
    largest_win         DECIMAL(12,2),
    largest_loss        DECIMAL(12,2),
    total_pnl           DECIMAL(14,2),

    -- Risk-adjusted
    sharpe_ratio        DECIMAL(8,4),
    sortino_ratio       DECIMAL(8,4),
    max_drawdown_dollar DECIMAL(12,2),
    max_drawdown_pct    DECIMAL(8,4),

    -- Behavioral
    avg_hold_time_minutes INTEGER,
    max_consec_wins     INTEGER DEFAULT 0,
    max_consec_losses   INTEGER DEFAULT 0,

    -- Compliance
    avg_compliance_score DECIMAL(5,2),

    -- Metadata
    last_calculated_at  TIMESTAMPTZ DEFAULT NOW(),
    trade_hash          VARCHAR(64), -- Hash of trade IDs + PnLs for change detection

    CONSTRAINT unique_playbook_period UNIQUE (playbook_id, period_type)
);

CREATE INDEX idx_pm_playbook ON playbook_metrics (playbook_id);

-- Playbook equity curve data points
CREATE TABLE playbook_equity_curve (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playbook_id     UUID NOT NULL REFERENCES playbooks(id),
    trade_id        UUID NOT NULL REFERENCES trades(id),
    trade_close_at  TIMESTAMPTZ NOT NULL,
    trade_pnl       DECIMAL(12,2) NOT NULL,
    trade_r         DECIMAL(8,4),
    cumulative_pnl  DECIMAL(14,2) NOT NULL,
    cumulative_r    DECIMAL(10,4),
    drawdown_dollar DECIMAL(12,2),
    drawdown_pct    DECIMAL(8,4),
    equity_peak     DECIMAL(14,2),

    CONSTRAINT unique_curve_point UNIQUE (playbook_id, trade_id)
);

CREATE INDEX idx_pec_playbook_time
    ON playbook_equity_curve (playbook_id, trade_close_at);

-- Classification audit log (immutable)
CREATE TABLE classification_audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id            UUID NOT NULL REFERENCES trades(id),
    from_playbook_id    UUID REFERENCES playbooks(id),
    to_playbook_id      UUID NOT NULL REFERENCES playbooks(id),
    from_method         VARCHAR(10),
    to_method           VARCHAR(10) NOT NULL,
    changed_by          UUID NOT NULL REFERENCES users(id),
    reason              TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cal_trade ON classification_audit_log (trade_id);

-- Playbook templates
CREATE TABLE playbook_templates (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by              UUID NOT NULL REFERENCES users(id),
    org_id                  UUID REFERENCES organizations(id),
    name                    VARCHAR(100) NOT NULL,
    description             TEXT,
    criteria_description    TEXT NOT NULL,
    auto_classify_rules     JSONB,
    compliance_checklist    JSONB,
    risk_overrides          JSONB,
    version                 INTEGER DEFAULT 1,
    usage_count             INTEGER DEFAULT 0,
    is_shared               BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pt_org ON playbook_templates (org_id) WHERE org_id IS NOT NULL;
```

### 5.2 Row-Level Security (RLS)

```sql
-- Users can only access their own playbooks
ALTER TABLE playbooks ENABLE ROW LEVEL SECURITY;

CREATE POLICY playbooks_user_isolation ON playbooks
    USING (
        user_id = auth.uid()
        OR (is_shared = TRUE AND org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        ))
    );

-- Trade assignments follow playbook access
ALTER TABLE trade_playbook_assignments ENABLE ROW LEVEL SECURITY;

CREATE POLICY tpa_user_isolation ON trade_playbook_assignments
    USING (
        trade_id IN (SELECT id FROM trades WHERE user_id = auth.uid())
    );

-- Metrics follow playbook access
ALTER TABLE playbook_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY pm_user_isolation ON playbook_metrics
    USING (
        playbook_id IN (SELECT id FROM playbooks WHERE user_id = auth.uid()
            OR (is_shared = TRUE AND org_id IN (
                SELECT org_id FROM org_members WHERE user_id = auth.uid()
            )))
    );
```

### 5.3 Entity Relationship Summary

```
User (1) ---< (many) Playbook
Playbook (1) ---< (many) Trade (via trade_playbook_assignments)
Playbook (1) ---< (many) PlaybookMetrics (one per period_type)
Playbook (1) ---< (many) PlaybookEquityCurve (one per closed trade)
Trade (1) --- (1) TradePlaybookAssignment
Trade (1) ---< (many) ClassificationAuditLog
Playbook (0..1) ---< (many) PlaybookTemplate
Organization (1) ---< (many) Playbook (shared, Team tier)
```

---

## 6. API Specification

### 6.1 Playbook CRUD Endpoints

| Method | Path | Description | Auth | Tier |
|---|---|---|---|---|
| `POST` | `/api/v1/playbooks` | Create a custom playbook | Required | Trader+ |
| `GET` | `/api/v1/playbooks` | List all playbooks (active + archived) | Required | All |
| `GET` | `/api/v1/playbooks/{id}` | Get playbook detail with metrics | Required | All |
| `PATCH` | `/api/v1/playbooks/{id}` | Update a custom playbook | Required | Trader+ |
| `DELETE` | `/api/v1/playbooks/{id}` | Delete a playbook (0 trades only) | Required | Trader+ |
| `POST` | `/api/v1/playbooks/{id}/archive` | Archive a playbook | Required | All |
| `POST` | `/api/v1/playbooks/{id}/unarchive` | Unarchive a playbook | Required | All |

### 6.2 Classification Endpoints

| Method | Path | Description | Auth | Tier |
|---|---|---|---|---|
| `POST` | `/api/v1/playbooks/classify` | Auto-classify a trade (called by execution pipeline) | Internal | N/A |
| `POST` | `/api/v1/playbooks/test-classify` | Test classification with mock data | Required | Trader+ |
| `POST` | `/api/v1/trades/{id}/assign-playbook` | Manually assign/reassign trade to playbook | Required | All |
| `POST` | `/api/v1/trades/bulk-assign-playbook` | Bulk reassign trades | Required | Trader+ |

### 6.3 Metrics and Comparison Endpoints

| Method | Path | Description | Auth | Tier |
|---|---|---|---|---|
| `GET` | `/api/v1/playbooks/{id}/metrics` | Get playbook metrics (with date range params) | Required | All |
| `GET` | `/api/v1/playbooks/{id}/equity-curve` | Get equity curve data points | Required | All |
| `GET` | `/api/v1/playbooks/compare` | Compare metrics across selected playbooks | Required | Trader+ |

### 6.4 Template Endpoints

| Method | Path | Description | Auth | Tier |
|---|---|---|---|---|
| `POST` | `/api/v1/playbook-templates` | Save playbook as template | Required | Pro+ |
| `GET` | `/api/v1/playbook-templates` | List available templates (personal + team) | Required | Pro+ |
| `POST` | `/api/v1/playbook-templates/{id}/instantiate` | Create playbook from template | Required | Pro+ |
| `DELETE` | `/api/v1/playbook-templates/{id}` | Delete a template | Required | Pro+ |

### 6.5 Example Request/Response

**POST /api/v1/playbooks**
```json
// Request
{
  "name": "High-Volume Breakouts",
  "description": "Trendline breaks with above-average volume on break candle",
  "criteria_description": "A+ trendline criteria met, plus break candle volume > 1.5x 20-period average volume. Only RTH sessions.",
  "auto_classify_rules": {
    "version": "1.0",
    "match_mode": "all",
    "conditions": [
      { "field": "touch_count", "operator": "gte", "value": 3 },
      { "field": "slope_angle", "operator": "lt", "value": 45 },
      { "field": "setup_type", "operator": "eq", "value": "break" },
      { "field": "session", "operator": "eq", "value": "rth" }
    ]
  },
  "priority": 10,
  "color": "#10B981",
  "risk_overrides": {
    "max_risk_per_trade_pct": 1.5,
    "min_rr_ratio": 2.5
  }
}

// Response (201 Created)
{
  "id": "b7a3f1e2-...",
  "user_id": "u1234...",
  "name": "High-Volume Breakouts",
  "slug": "high-volume-breakouts",
  "status": "active",
  "is_default": false,
  "trade_count": 0,
  "created_at": "2026-02-11T14:30:00Z",
  "...": "..."
}
```

**GET /api/v1/playbooks/compare?ids=pb1,pb2,pb3&period=90d**
```json
{
  "period": { "type": "90d", "start": "2025-11-13", "end": "2026-02-11" },
  "playbooks": [
    {
      "id": "pb1",
      "name": "A+ Trendline Break",
      "metrics": {
        "trade_count": 12,
        "win_rate": 0.6667,
        "avg_r_multiple": 1.85,
        "profit_factor": 3.21,
        "expectancy": 482.50,
        "expectancy_r": 1.23,
        "sharpe_ratio": 1.45,
        "sortino_ratio": 2.10,
        "avg_hold_time_minutes": 4320,
        "max_consec_wins": 4,
        "max_consec_losses": 2,
        "total_pnl": 5790.00,
        "max_drawdown_dollar": -1250.00,
        "avg_compliance_score": 92.5
      }
    },
    {
      "id": "pb2",
      "name": "Standard Trendline Break",
      "metrics": { "...": "..." }
    }
  ]
}
```

---

## 7. Dependencies

### 7.1 Upstream Dependencies (This PRD Depends On)

| PRD | System | Dependency Type | Details |
|---|---|---|---|
| PRD-002 | Trendline Detection Engine | Data | Auto-classification consumes trendline metadata: `touch_count`, `slope_angle`, `candle_spacing_min`, `trendline_duration_weeks`, `trendline_grade`, `setup_type`. If PRD-002 is unavailable, trades fall through to "Custom / Manual". |
| PRD-003 | Trade Execution Pipeline | Event | Auto-classification is triggered by the `trade.created` event emitted by the execution pipeline. Playbook risk overrides (PB-FR-036) feed back into PRD-003's risk check step. |
| PRD-004 | Trade Journaling | Data + UI | Manual playbook assignment occurs within the journal entry UI. Compliance checklist items with `auto_check: false` are rendered in the journal enrichment form. |
| Core | User / Auth / Billing | Infrastructure | Tier enforcement, user isolation, organization membership for team sharing. |

### 7.2 Downstream Dependencies (Other PRDs Depend On This)

| PRD | System | Dependency Type | Details |
|---|---|---|---|
| PRD-006 | Performance Analytics | Data | Aggregate analytics consume per-playbook metrics. Playbook-level filtering and drill-down require the playbook assignment on each trade. Equity curve overlay uses `playbook_equity_curve` data. |
| PRD-003 | Trade Execution Pipeline | Data | Execution pipeline reads `risk_overrides` from the matched playbook to apply playbook-specific position sizing and risk limits. |

### 7.3 Dependency Availability Strategy

- **PRD-002 unavailable at trade creation**: Trade is assigned to "Custom / Manual" with a system note `"classification_note": "trendline_metadata_unavailable"`. The trade can be manually reclassified later.
- **PRD-003 unavailable**: Playbook system is unaffected (it only reads from trades, does not create them).
- **PRD-004 unavailable**: Playbook assignment still occurs via auto-classification. Manual assignment and compliance checks are deferred until journal entry is created.

---

## 8. Testing Requirements

### 8.1 Auto-Classification Accuracy

| Test ID | Scenario | Expected Result |
|---|---|---|
| PB-T-001 | Trade with 3 touches, 40-degree slope, 8-candle spacing, break setup, 4-week duration | Classified as "A+ Trendline Break" |
| PB-T-002 | Trade with 2 touches, break setup | Classified as "Standard Trendline Break" |
| PB-T-003 | Trade with 3 touches, bounce setup | Classified as "Trendline Bounce" |
| PB-T-004 | Trade with 2 touches, bounce setup | Classified as "Trendline Bounce" (bounce takes precedence over touch count) |
| PB-T-005 | Trade with no trendline metadata (manual entry) | Classified as "Custom / Manual" |
| PB-T-006 | Trade matching both a custom rule (priority 10) and A+ default | Classified into the custom playbook (lower priority number wins) |
| PB-T-007 | Trade matching no active playbook rules | Classified as "Custom / Manual" |
| PB-T-008 | Trade created when trendline engine is down | Classified as "Custom / Manual" with system note |
| PB-T-009 | Trade with 5 touches, 50-degree slope, break setup | Classified as "Standard Trendline Break" (slope exceeds A+ threshold of 45 degrees) |
| PB-T-010 | Trade with 3 touches, 30-degree slope, 4-candle spacing, break setup | Classified as "Standard Trendline Break" (candle spacing below A+ threshold of 6) |

### 8.2 Metrics Calculation Correctness

| Test ID | Scenario | Validation |
|---|---|---|
| PB-T-011 | Playbook with 3 wins (+2R, +1R, +3R) and 2 losses (-1R, -1R) | Win rate = 0.60, avg R = 0.80, profit factor = 3.0, expectancy_r = 0.80 |
| PB-T-012 | Playbook with only wins | Profit factor = infinity (display as "N/A" or max cap), no avg_loser |
| PB-T-013 | Playbook with only losses | Profit factor = 0, no avg_winner |
| PB-T-014 | Playbook with 0 closed trades | All metrics show "Insufficient data" |
| PB-T-015 | Playbook with 5 trades (below Sharpe threshold of 10) | Sharpe/Sortino show "Insufficient data", other metrics calculated |
| PB-T-016 | Equity curve for 5 trades: +100, -50, +200, -75, +150 | Cumulative: 100, 50, 250, 175, 325. Max drawdown = -75 (from 250 to 175) |
| PB-T-017 | Consecutive wins/losses: W, W, L, W, W, W, L, L | max_consec_wins = 3, max_consec_losses = 2 |
| PB-T-018 | Metrics after reclassifying a trade out | Source playbook metrics decrease, destination playbook metrics increase. Both are correct. |
| PB-T-019 | Idempotent recalculation | Running metrics calculation twice on same data produces identical results |

### 8.3 Playbook CRUD Operations

| Test ID | Scenario | Expected Result |
|---|---|---|
| PB-T-020 | Create playbook with valid data | 201 Created, playbook appears in list |
| PB-T-021 | Create playbook with duplicate name | 409 Conflict, descriptive error |
| PB-T-022 | Create playbook exceeding tier limit | 403 Forbidden, upgrade prompt |
| PB-T-023 | Update custom playbook name | 200 OK, name updated, slug updated |
| PB-T-024 | Update default playbook criteria | 403 Forbidden, immutable field |
| PB-T-025 | Delete playbook with 0 trades | 200 OK, playbook removed |
| PB-T-026 | Delete playbook with trades | 409 Conflict, must reassign or archive |
| PB-T-027 | Archive playbook | Status set to `archived`, removed from active list, trades preserved |
| PB-T-028 | Unarchive playbook within tier limit | Status set to `active`, restored to list |
| PB-T-029 | Unarchive playbook exceeding tier limit | 403 Forbidden, upgrade prompt |
| PB-T-030 | Delete "Custom / Manual" fallback | 403 Forbidden, cannot delete or archive |

### 8.4 Tier Limit Enforcement

| Test ID | Tier | Action | Expected Result |
|---|---|---|---|
| PB-T-031 | Free | Create custom playbook | 403, upgrade prompt |
| PB-T-032 | Free | Access locked default playbook metrics | 403, upgrade prompt |
| PB-T-033 | Trader | Create 6th custom playbook | 403, upgrade prompt |
| PB-T-034 | Trader | Compare 3+ playbooks | 403 (Trader limited to 2) |
| PB-T-035 | Pro | Create 51st playbook (cap) | 403, limit reached |
| PB-T-036 | Pro | Save playbook as template | 200 OK |
| PB-T-037 | Trader | Save playbook as template | 403, Pro+ required |
| PB-T-038 | Team | Share playbook with org member | 200 OK |
| PB-T-039 | Pro | Share playbook | 403, Team tier required |
| PB-T-040 | Trader, downgraded from Pro | Access 10 existing custom playbooks | Read-only access to all, cannot create new until under limit |

### 8.5 Edge Cases

| Test ID | Scenario | Expected Result |
|---|---|---|
| PB-T-041 | Trade matches multiple custom rules with same priority | First rule by `created_at` wins (deterministic ordering) |
| PB-T-042 | All playbooks are archived except "Custom / Manual" | New trades go to "Custom / Manual" |
| PB-T-043 | Auto-classify rule references a field not present in trade metadata | Condition evaluates to false, continues to next condition/playbook |
| PB-T-044 | Playbook with `match_mode: "any"` and 3 conditions, 1 matches | Trade classified into that playbook |
| PB-T-045 | Trade reclassified back to its original playbook | Reclassification succeeds, audit log records the roundtrip |
| PB-T-046 | Concurrent reclassification of same trade by two sessions | Database constraint ensures exactly one assignment; second request fails with 409 |
| PB-T-047 | Playbook metrics requested during recalculation | Return last cached metrics with `stale: true` flag |
| PB-T-048 | User creates playbook, downgrades tier, then tries to edit | Read-only access, cannot modify. Must upgrade or archive excess playbooks. |
| PB-T-049 | Bulk reclassify 500 trades where target playbook is archived mid-operation | Operation fails atomically, no partial reclassification |
| PB-T-050 | Rule with `match_mode: "all"` and empty conditions array | Validation error on save (PB-FR-020 requires at least one condition) |

### 8.6 Integration Tests

| Test ID | Systems | Scenario | Expected Result |
|---|---|---|---|
| PB-T-051 | PRD-002 + PRD-005 | Trendline engine detects A+ break, trade created | Trade auto-classified to "A+ Trendline Break" with correct metadata snapshot |
| PB-T-052 | PRD-003 + PRD-005 | Trade signal matches playbook with risk overrides | Execution pipeline uses playbook risk limits for position sizing |
| PB-T-053 | PRD-004 + PRD-005 | User creates manual journal entry | Journal UI shows playbook dropdown, defaults to "Custom / Manual" |
| PB-T-054 | PRD-005 + PRD-006 | Playbook metrics updated | Analytics dashboard reflects updated per-playbook data within 10 seconds |

---

## 9. Security

### 9.1 User Isolation

**PB-SEC-001**: All playbook data SHALL be isolated per user via PostgreSQL Row-Level Security (RLS). A user SHALL never be able to read, write, or enumerate another user's playbooks, trades, or metrics, except through explicit Team tier sharing.

**PB-SEC-002**: API endpoints SHALL validate that the authenticated user owns the requested playbook before performing any operation. This is enforced at both the application layer (FastAPI dependency injection) and the database layer (RLS policies).

**PB-SEC-003**: The `classify` internal endpoint SHALL only be callable by the execution pipeline service (service-to-service authentication via API key or JWT with `service` role). It SHALL NOT be exposed to end users.

### 9.2 Team Sharing Permissions

**PB-SEC-004**: Shared playbook access SHALL be gated by organization membership. When a user is removed from an organization, their access to all shared playbooks in that organization SHALL be revoked immediately.

**PB-SEC-005**: Team members with "View" permission on a shared playbook SHALL NOT be able to:
- Modify the playbook configuration.
- Assign their trades to the shared playbook.
- View individual trade details of other members (only aggregate metrics).

**PB-SEC-006**: Team members with "Use" permission SHALL be able to assign their own trades to the shared playbook and view their own individual metrics, but SHALL NOT be able to view other members' individual trade details unless the team admin has enabled member-level visibility.

### 9.3 Data Protection

**PB-SEC-007**: Auto-classification rule snapshots stored with trades (`matched_rule_snapshot`) SHALL NOT contain sensitive data. Rules only reference metadata field names, operators, and threshold values.

**PB-SEC-008**: The classification audit log SHALL be append-only. No API endpoint SHALL allow deletion or modification of audit log entries.

**PB-SEC-009**: Playbook templates shared within a team SHALL NOT include any trade data, P&L information, or user-specific metadata. Templates contain only structural configuration.

### 9.4 Input Validation

**PB-SEC-010**: All JSON fields (`auto_classify_rules`, `risk_overrides`, `compliance_checklist`) SHALL be validated against their respective JSON schemas on every write operation. Malformed or unexpected keys SHALL be rejected with a 422 Unprocessable Entity response.

**PB-SEC-011**: Playbook names and descriptions SHALL be sanitized to prevent XSS when rendered in the frontend. HTML tags SHALL be stripped on save.

---

## 10. Phase Mapping

### Phase 1: Personal Trading System (Weeks 9-10)

| Requirement | Description |
|---|---|
| PB-FR-001, PB-FR-002 | Seed default playbooks and Custom / Manual fallback |
| PB-FR-003 | Immutable default classification rules |
| PB-FR-015, PB-FR-016, PB-FR-017, PB-FR-018 | Auto-classification engine with default rules |
| PB-FR-021 | Classify trades on creation |
| PB-FR-023, PB-FR-024 | Manual playbook assignment |
| PB-FR-028 (core metrics only) | Win rate, avg R, profit factor, expectancy, trade count |
| PB-FR-029 | Basic equity curve per playbook |
| PB-NFR-001, PB-NFR-009 | Classification latency and data integrity |
| Database schema | Full schema deployed (future features use empty columns) |

### Phase 2: Analytics and Journaling (Weeks 11-14)

| Requirement | Description |
|---|---|
| PB-FR-005 through PB-FR-010 | Custom playbook CRUD |
| PB-FR-011 through PB-FR-014 | Playbook archiving |
| PB-FR-019, PB-FR-020 | Custom rule priorities and validation |
| PB-FR-022 | Test classification endpoint |
| PB-FR-025, PB-FR-026, PB-FR-027 | Trade reclassification (single and bulk) |
| PB-FR-028 (all metrics) | Sharpe, Sortino, max drawdown, behavioral metrics |
| PB-FR-030, PB-FR-031, PB-FR-032 | Metrics recalculation, minimums, date filtering |
| PB-FR-033, PB-FR-034 | Playbook comparison view |
| PB-FR-035, PB-FR-036, PB-FR-037 | Playbook-specific risk parameters |
| PB-FR-038, PB-FR-039, PB-FR-040, PB-FR-041 | Rule compliance tracking |
| PB-NFR-002 through PB-NFR-008 | Performance and scalability requirements |
| PB-NFR-014, PB-NFR-015 | Usability: fast creation, visual rule builder |

### Phase 3: Multi-Tenant SaaS Launch (Weeks 15-22)

| Requirement | Description |
|---|---|
| PB-FR-004, PB-FR-009 | Tier limit enforcement |
| PB-FR-042, PB-FR-043 | Playbook templates (Pro tier) |
| PB-FR-044, PB-FR-045 | Team template sharing |
| PB-FR-046 through PB-FR-049 | Team playbook sharing with permissions |
| PB-SEC-001 through PB-SEC-011 | Full security model with RLS and team permissions |
| PB-NFR-010, PB-NFR-011, PB-NFR-012, PB-NFR-013 | Data integrity, availability, caching |

### Phase 4: Growth and Advanced Features (Months 6-12)

| Requirement | Description |
|---|---|
| Future | Public playbook marketplace |
| Future | AI-suggested playbook classification improvements |
| Future | Cross-user anonymized playbook benchmarking |
| Future | Playbook decay detection (rolling window analysis surfaced as alerts) |

---

## 11. Acceptance Criteria

### 11.1 Phase 1 Acceptance (Weeks 9-10)

- [ ] Three default playbooks and one "Custom / Manual" fallback are seeded on user creation.
- [ ] A trade created by the trendline engine with A+ metadata is automatically classified to "A+ Trendline Break" within 2 seconds.
- [ ] A trade created by the trendline engine with 2-touch break metadata is automatically classified to "Standard Trendline Break".
- [ ] A trade with bounce metadata is classified to "Trendline Bounce".
- [ ] A manually entered trade with no trendline metadata is classified to "Custom / Manual".
- [ ] A user can manually reassign a trade to a different playbook via the journal UI.
- [ ] Each playbook displays win rate, average R-multiple, profit factor, expectancy, and trade count independently.
- [ ] Each playbook has a visible equity curve tracking cumulative P&L over time.
- [ ] No trade exists without a playbook assignment (enforced by database constraint).

### 11.2 Phase 2 Acceptance (Weeks 11-14)

- [ ] A Trader-tier user can create, read, update, and archive custom playbooks up to their tier limit.
- [ ] Custom playbooks with auto-classification rules are evaluated before default playbooks (priority ordering works correctly).
- [ ] The "test classification" endpoint returns the correct matched playbook for a given mock payload.
- [ ] A user can bulk-reassign up to 500 trades to a new playbook, and metrics for both source and destination playbooks are recalculated correctly within 30 seconds.
- [ ] Archived playbooks are excluded from active views and auto-classification but their historical data remains accessible.
- [ ] The comparison view shows side-by-side metrics for 2+ playbooks with best/worst highlighting.
- [ ] Overlaid equity curves render correctly for up to 5 playbooks.
- [ ] Sharpe ratio and Sortino ratio are calculated for playbooks with 10+ closed trades and show "Insufficient data" for fewer.
- [ ] Compliance checklist items (auto and manual) produce a per-trade compliance score and a rolling playbook compliance rate.
- [ ] Compliance-vs-outcome analysis correctly shows average P&L for high-compliance vs. low-compliance trades.
- [ ] Playbook risk overrides are picked up by the execution pipeline for position sizing.
- [ ] The visual rule builder generates valid JSON rules and can parse existing rules back into the visual editor.
- [ ] Metrics recalculation is triggered within 5 seconds of any trade update event.

### 11.3 Phase 3 Acceptance (Weeks 15-22)

- [ ] Free-tier user can only access 1 default playbook and the Custom / Manual fallback; other defaults are locked.
- [ ] Trader-tier user cannot create more than 5 custom playbooks; a clear upgrade prompt is shown.
- [ ] Pro-tier user can save a playbook as a template and instantiate new playbooks from templates.
- [ ] Team-tier admin can share a playbook with team members and control view/use permissions.
- [ ] Team aggregate metrics correctly combine trades from all members using a shared playbook.
- [ ] When a member leaves a team, their trades remain in the shared playbook history but the member loses access to team views.
- [ ] All playbook data is isolated per user via RLS; no cross-tenant data leakage (verified by security test).
- [ ] Downgrading from a higher tier preserves existing playbooks in read-only mode; the user cannot create or modify playbooks until within their new tier's limit.
- [ ] All JSON inputs are validated against schemas; malformed payloads return 422 with descriptive errors.

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| **Playbook** | A named strategy container that groups trades by shared entry criteria for independent performance tracking. |
| **Auto-classification** | Rule-based assignment of a trade to a playbook using trendline engine metadata, without user intervention. |
| **R-multiple** | Trade P&L expressed as a multiple of initial risk. A +2R trade earned twice the amount risked. |
| **Expectancy** | The average dollar amount (or R-multiple) expected to be won or lost per trade over a large sample. |
| **Profit Factor** | Ratio of gross profits to gross losses. Values above 1.0 indicate a profitable strategy. |
| **Sharpe Ratio** | Risk-adjusted return metric: excess return per unit of total volatility. Annualized by multiplying by sqrt(252). |
| **Sortino Ratio** | Like Sharpe but penalizes only downside volatility, making it more suitable for asymmetric return distributions. |
| **MAE/MFE** | Maximum Adverse Excursion / Maximum Favorable Excursion: worst and best unrealized P&L during a trade. |
| **Compliance Score** | Percentage of checklist items satisfied for a trade within its assigned playbook (0-100%). |
| **Safety Line** | The opposing trendline projected forward by 4 candles, used as stop-loss placement in the Tori Trades methodology. |

## Appendix B: Related PRDs

| PRD | Title | Relationship |
|---|---|---|
| PRD-001 | System Architecture and Infrastructure | Foundation: database, auth, API framework |
| PRD-002 | Trendline Detection Engine | Upstream: provides metadata for auto-classification |
| PRD-003 | Trade Execution Pipeline | Upstream: creates trades; Downstream: consumes risk overrides |
| PRD-004 | Trade Journaling | Upstream: provides journal UI for manual assignment and compliance |
| PRD-005 | Playbook System | This document |
| PRD-006 | Performance Analytics | Downstream: consumes per-playbook metrics and equity curves |
| PRD-007 | AI-Powered Features | Downstream: conversational queries reference playbook data |
| PRD-008 | Notification System | Downstream: playbook-specific alert preferences |
| PRD-009 | Multi-Account and Prop Firm Support | Downstream: playbook metrics per account |
| PRD-010 | Billing and Subscription Management | Upstream: tier limits for playbook features |
| PRD-011 | Mobile Application | Downstream: playbook views on mobile |
