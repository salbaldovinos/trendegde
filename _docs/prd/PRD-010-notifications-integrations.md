# PRD-010: Notifications & External Integrations

**TrendEdge — AI-Powered Futures Trading Platform**
PRD-010 of 11 | Version 1.0 | February 2026 | CONFIDENTIAL

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
   - 3.1 [Notification Engine (Central Dispatch)](#31-notification-engine-central-dispatch)
   - 3.2 [Telegram Bot Integration](#32-telegram-bot-integration)
   - 3.3 [Discord Webhook Integration](#33-discord-webhook-integration)
   - 3.4 [Email Notifications (SendGrid/Resend)](#34-email-notifications-sendgridresend)
   - 3.5 [TradingView Webhook Receiver](#35-tradingview-webhook-receiver)
   - 3.6 [In-App Notification Center](#36-in-app-notification-center)
   - 3.7 [Market Data Integration](#37-market-data-integration)
   - 3.8 [Notification Preferences Management UI](#38-notification-preferences-management-ui)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Dependencies](#5-dependencies)
6. [Testing Requirements](#6-testing-requirements)
7. [Security](#7-security)
8. [Phase Mapping](#8-phase-mapping)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. Overview & Purpose

### Problem Statement

Futures swing traders need reliable, multi-channel, real-time awareness of trade events, market alerts, and platform activity. Today they check multiple apps, miss critical fill notifications, and lose context between their TradingView charts, broker platforms, and journaling tools. There is no single system that centralizes all trading notifications with tier-appropriate channel routing and accepts inbound signals from external charting platforms.

### Purpose

This PRD defines TrendEdge's notification and external integration layer -- the system that connects TrendEdge's internal events (trendline alerts, trade fills, P&L summaries) to outbound delivery channels (Telegram, Discord, email, in-app) and accepts inbound signals from external platforms (TradingView webhooks). It also covers market data integrations that feed the trendline detection and analytics engines.

### Scope

**In Scope:**
- Central notification dispatch engine with event-driven triggers, channel routing, templates, retry logic, and rate limiting
- Telegram Bot: real-time alerts, interactive commands, manual trade entry
- Discord Webhook: trade signal embeds, leaderboard updates, daily summaries
- Email (SendGrid/Resend): transactional emails, daily/weekly digest emails
- TradingView webhook receiver: inbound signal ingestion with validation and symbol mapping
- In-app notification center: real-time WebSocket delivery, notification history, read/unread tracking
- Market data integrations: historical OHLCV (yfinance), real-time broker data, sentiment data pipeline
- Notification preferences management UI

**Out of Scope:**
- Push notifications for native mobile app (Phase 4 -- see PRD roadmap)
- SMS notifications (not planned)
- Slack integration (potential future addition)
- Pine Script companion indicator development (marketing asset, separate initiative)
- Trading strategy logic (covered in PRD-002)
- Order execution logic (covered in PRD-003)

### Key Design Principles

1. **Event-driven, not poll-driven.** Every notification originates from a domain event. The notification engine subscribes to events; it never polls for state changes.

2. **Channel-agnostic core.** The dispatch engine knows nothing about Telegram message formatting or Discord embed structures. Channel adapters handle all formatting. Adding a new channel requires only a new adapter, not engine changes.

3. **Tier-gated delivery.** Channel access is enforced at the dispatch layer based on the user's subscription tier. A Free user's trade fill event produces only an email notification; a Pro user's identical event fans out to Telegram, Discord, email, and in-app simultaneously.

4. **Delivery guarantees for critical events.** Trade fills and risk limit breaches require at-least-once delivery with retry. Marketing and informational notifications are best-effort.

5. **Respect user attention.** Rate limiting, quiet hours, and granular per-event-type preferences prevent notification fatigue.

---

## 2. User Stories

### Notification Delivery

| ID | Story | Priority |
|---|---|---|
| US-NT-001 | As a trader, I want to receive an instant Telegram message when my bracket order is filled so I know my trade is live without checking my broker. | P0 |
| US-NT-002 | As a trader, I want to receive a daily P&L summary at market close on Telegram so I can review my day without logging into the dashboard. | P0 |
| US-NT-003 | As a trader, I want a weekly performance digest email with equity curve, win rate, and top/bottom trades so I can review my week during the weekend. | P1 |
| US-NT-004 | As a trader, I want to mute all notifications during specific hours (quiet hours) so I am not disturbed outside trading sessions. | P1 |
| US-NT-005 | As a trader, I want to choose which event types go to which channels so I only get Telegram messages for fills but email for digests. | P1 |
| US-NT-006 | As a free-tier user, I want to receive email notifications for critical events so I am not entirely left in the dark. | P0 |

### Telegram Bot

| ID | Story | Priority |
|---|---|---|
| US-NT-007 | As a trader, I want to link my Telegram account to TrendEdge through a one-time code so the bot knows who I am. | P0 |
| US-NT-008 | As a trader, I want to type `/status` in Telegram and see my open positions, unrealized P&L, and daily P&L so I can check my status from my phone. | P0 |
| US-NT-009 | As a trader, I want to type `/pause` to temporarily halt all automated execution and `/resume` to re-enable it, providing a safety valve. | P0 |
| US-NT-010 | As a trader, I want to enter a manual trade via Telegram (`/trade BUY MES 5200 SL:5190 TP:5220`) so I can act on setups when away from my computer. | P1 |
| US-NT-011 | As a trader, I want interactive inline keyboard buttons on fill notifications (e.g., "Move Stop to BE", "Close Position") so I can manage trades from Telegram. | P2 |

### Discord Integration

| ID | Story | Priority |
|---|---|---|
| US-NT-012 | As a trader, I want my trade signals posted to my Discord server so my community can see my activity in real time. | P1 |
| US-NT-013 | As a community leader, I want daily and weekly summary embeds posted to Discord with key metrics and leaderboard standings. | P1 |
| US-NT-014 | As a trader, I want to configure my Discord webhook URL in settings and preview the embed format before going live. | P1 |

### TradingView Integration

| ID | Story | Priority |
|---|---|---|
| US-NT-015 | As a trader, I want a unique webhook URL I can paste into TradingView alerts so my TradingView signals automatically trigger trades in TrendEdge. | P0 |
| US-NT-016 | As a trader, I want TrendEdge to map TradingView continuous contract symbols (NQ1!, ES1!) to the correct broker-specific contract (MNQH26, MESH26) so my orders go to the right instrument. | P0 |
| US-NT-017 | As a trader, I want to see a log of all received webhooks with status (accepted/rejected/error) so I can debug alert configuration issues. | P0 |
| US-NT-018 | As a trader, I want to regenerate my webhook URL and API key if I suspect they have been compromised. | P1 |

### In-App Notifications

| ID | Story | Priority |
|---|---|---|
| US-NT-019 | As a trader, I want to see a notification bell in the dashboard header with an unread count badge so I know when new events have occurred. | P1 |
| US-NT-020 | As a trader, I want to open a notification panel that shows my recent notifications with timestamps, and I want to mark them as read individually or all at once. | P1 |
| US-NT-021 | As a trader, I want notifications to appear in real time (without page refresh) via WebSocket so I see fills and alerts the moment they happen. | P1 |

### Market Data

| ID | Story | Priority |
|---|---|---|
| US-NT-022 | As a trader, I want TrendEdge to fetch historical daily OHLCV data for my instruments so the trendline engine can run without me providing data files. | P0 |
| US-NT-023 | As a trader, I want real-time price updates from my connected broker so the dashboard shows current prices and unrealized P&L. | P0 |
| US-NT-024 | As a pro trader, I want daily sentiment scores derived from market headlines so I can incorporate sentiment into my decision-making. | P2 |

---

## 3. Functional Requirements

### 3.1 Notification Engine (Central Dispatch)

The notification engine is the central nervous system for all outbound communications. It receives domain events, resolves the target user's channel preferences and tier, renders channel-specific templates, dispatches messages to channel adapters, and tracks delivery status.

#### Event-Driven Notification Triggers

**NT-FR-001:** The notification engine SHALL subscribe to the following domain events via Redis Pub/Sub or an internal event bus:

| Event | Source | Criticality | Description |
|---|---|---|---|
| `trade.fill` | Execution engine | Critical | Order filled (entry or exit) |
| `trade.rejected` | Execution engine | Critical | Order rejected by broker |
| `trade.closed` | Execution engine | Critical | Position fully closed (P&L finalized) |
| `risk.limit_breach` | Risk engine | Critical | Daily loss limit, max position, or drawdown limit hit |
| `risk.warning` | Risk engine | High | Approaching risk limit (80% threshold) |
| `trendline.alert` | Trendline engine | High | Trendline break, touch, or new A+ detection |
| `trendline.invalidated` | Trendline engine | Medium | Previously qualifying trendline broken without entry |
| `webhook.received` | Webhook receiver | Medium | Inbound TradingView webhook processed |
| `webhook.error` | Webhook receiver | High | Inbound webhook validation failure |
| `account.connection_lost` | Broker adapter | Critical | Broker API connection dropped |
| `account.connection_restored` | Broker adapter | High | Broker API connection re-established |
| `digest.daily` | Scheduler (Celery Beat) | Low | Trigger for daily P&L digest generation |
| `digest.weekly` | Scheduler (Celery Beat) | Low | Trigger for weekly performance digest generation |
| `system.maintenance` | Admin | Medium | Scheduled maintenance window approaching |
| `subscription.changed` | Billing | Medium | User's subscription tier changed |
| `paper.milestone` | Analytics engine | Low | Paper trading milestone reached (e.g., 60-day mark) |

**NT-FR-002:** Each event payload SHALL include at minimum: `event_type`, `user_id`, `timestamp` (ISO 8601 UTC), `payload` (event-specific data), and `correlation_id` (for tracing across systems).

**NT-FR-003:** The engine SHALL be implemented as a Celery worker consuming from a dedicated `notifications` queue, decoupled from the event-producing services to prevent notification processing from blocking trade execution.

#### Channel Routing

**NT-FR-004:** The engine SHALL resolve the target user's notification preferences to determine which channels to dispatch to for each event type. Resolution follows this priority chain:

1. Check if user has explicitly disabled this event type entirely -- if yes, skip.
2. Check if quiet hours are active for the user -- if yes, queue for deferred delivery (except Critical events).
3. Check user's subscription tier to determine available channels.
4. Check user's per-event-type channel preferences to determine target channels.
5. Dispatch to each enabled and available channel.

**NT-FR-005:** Channel availability SHALL be enforced by subscription tier:

| Channel | Free | Trader ($49/mo) | Pro ($99/mo) | Team ($199/mo) |
|---|---|---|---|---|
| Email | Yes | Yes | Yes | Yes |
| In-App | Yes | Yes | Yes | Yes |
| Telegram | No | Yes | Yes | Yes |
| Discord | No | No | Yes | Yes |
| Custom Webhooks | No | No | No | Yes |

**NT-FR-006:** When a user attempts to configure a channel not available on their tier, the UI SHALL display the channel as locked with a prompt: "Upgrade to {required_tier} to enable {channel_name} notifications" with a link to the billing page.

**NT-FR-007:** When a user downgrades their subscription tier, the engine SHALL automatically disable channels no longer available on the new tier and send a single email notification listing the disabled channels with an upgrade link.

#### Notification Templates

**NT-FR-008:** Each event type SHALL have a dedicated template per channel. Templates SHALL be stored as Jinja2 templates (for email HTML) and Python format strings (for Telegram/Discord) in a `templates/notifications/` directory.

**NT-FR-009:** Template variables SHALL be populated from the event payload. The template engine SHALL support the following variable categories:

| Category | Variables | Example |
|---|---|---|
| Trade | `symbol`, `direction`, `quantity`, `entry_price`, `exit_price`, `stop_loss`, `take_profit`, `pnl_dollars`, `pnl_ticks`, `r_multiple`, `slippage_ticks` | `BUY 2 MES @ 5,205.25` |
| Trendline | `instrument`, `touch_count`, `slope_degrees`, `duration_days`, `grade`, `alert_type` | `A+ Trendline Break on ES (4 touches, 32 days)` |
| Account | `daily_pnl`, `weekly_pnl`, `open_positions_count`, `unrealized_pnl`, `daily_loss_remaining` | `Daily P&L: +$425.00 (3W/1L)` |
| Risk | `limit_type`, `current_value`, `limit_value`, `percent_used` | `Daily loss limit 80% used ($800/$1,000)` |
| Meta | `timestamp_utc`, `timestamp_user_tz`, `platform_url`, `trade_id`, `signal_source` | Link to trade detail page |

**NT-FR-010:** Each template SHALL include a fallback plain-text version for channels that do not support rich formatting.

**NT-FR-011:** The `trade.fill` notification template for Telegram SHALL render as:

```
FILL: BUY 2 MES @ 5,205.25
Stop: 5,190.00 | Target: 5,225.50
Risk: $305.00 | R:R 1:2.03
Source: TradingView Webhook
Time: 2026-02-11 14:32:05 ET
```

**NT-FR-012:** The `trade.closed` notification template for Telegram SHALL render as:

```
CLOSED: SELL 2 MES @ 5,223.75
Entry: 5,205.25 | P&L: +$370.00 (+1.82R)
Duration: 4h 23m | Slippage: 0.5 ticks
Daily P&L: +$425.00 (3W / 1L)
```

#### Delivery Status Tracking

**NT-FR-013:** The system SHALL persist a `notification_log` record for every dispatch attempt with the following fields:

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Target user |
| `event_type` | VARCHAR(50) | Event that triggered this notification |
| `channel` | VARCHAR(20) | `telegram`, `discord`, `email`, `in_app`, `custom_webhook` |
| `status` | VARCHAR(20) | `queued`, `dispatched`, `delivered`, `failed`, `deferred` |
| `payload` | JSONB | Rendered notification content |
| `attempt_count` | INTEGER | Number of delivery attempts |
| `last_error` | TEXT | Error message from most recent failed attempt |
| `created_at` | TIMESTAMPTZ | When the notification was created |
| `dispatched_at` | TIMESTAMPTZ | When the notification was sent to the channel |
| `delivered_at` | TIMESTAMPTZ | When delivery was confirmed (if channel supports confirmation) |
| `correlation_id` | UUID | Links back to originating event |

**NT-FR-014:** The notification log SHALL be queryable by user, event type, channel, status, and date range via the admin API and the user's notification history panel.

**NT-FR-015:** Notification log entries SHALL be retained for 90 days, then archived to cold storage (S3/R2). Critical event logs (`trade.fill`, `risk.limit_breach`) SHALL be retained for 1 year.

#### Retry Logic

**NT-FR-016:** Failed deliveries SHALL be retried with exponential backoff:

| Attempt | Delay | Max Elapsed |
|---|---|---|
| 1st retry | 10 seconds | 10s |
| 2nd retry | 30 seconds | 40s |
| 3rd retry | 2 minutes | 2m 40s |
| 4th retry | 10 minutes | 12m 40s |
| 5th retry (final) | 30 minutes | 42m 40s |

**NT-FR-017:** After all retry attempts are exhausted, the notification SHALL be marked `failed` in the notification log and the system SHALL:
- For Critical events: send a fallback notification via the next available channel in priority order (Telegram > In-App > Email).
- For non-Critical events: log the failure and take no further action.

**NT-FR-018:** Retries SHALL be implemented via Celery task retry with `max_retries=5` and `countdown` set per the backoff schedule above.

**NT-FR-019:** If a channel experiences 5+ consecutive failures across any user within a 5-minute window, the system SHALL activate a circuit breaker for that channel, pausing all dispatches for 2 minutes before attempting again. This prevents cascading failures when an external service (e.g., Telegram API) is down.

#### Rate Limiting

**NT-FR-020:** The notification engine SHALL enforce the following rate limits per user per channel:

| Channel | Rate Limit | Window | Burst |
|---|---|---|---|
| Telegram | 20 messages | Per hour | 5 in 1 minute |
| Discord | 10 messages | Per hour | 3 in 1 minute |
| Email | 5 emails | Per hour | 2 in 1 minute |
| In-App | 60 notifications | Per hour | No burst limit |
| Custom Webhook | 30 requests | Per hour | 5 in 1 minute |

**NT-FR-021:** When a rate limit is reached, non-Critical notifications SHALL be queued and batched into a single summary message delivered when the rate limit window resets. Critical notifications (`trade.fill`, `risk.limit_breach`, `account.connection_lost`) SHALL bypass rate limits.

**NT-FR-022:** Rate limit state SHALL be tracked in Redis using sliding window counters with keys following the pattern `ratelimit:{user_id}:{channel}:{window}`.

#### Quiet Hours / Do Not Disturb

**NT-FR-023:** Users SHALL be able to configure quiet hours with the following parameters:
- `enabled`: Boolean
- `start_time`: HH:MM in user's local timezone
- `end_time`: HH:MM in user's local timezone
- `timezone`: IANA timezone string (e.g., `America/New_York`)
- `days_of_week`: Array of integers 0-6 (Sunday-Saturday) specifying which days quiet hours apply
- `bypass_critical`: Boolean (default: `true`) -- whether Critical events bypass quiet hours

**NT-FR-024:** During active quiet hours, non-Critical notifications SHALL be deferred and delivered as a batched summary when quiet hours end. The summary message SHALL include a count and brief description of each deferred notification.

**NT-FR-025:** Critical events (`trade.fill`, `risk.limit_breach`, `account.connection_lost`) SHALL bypass quiet hours by default unless the user explicitly disables this via `bypass_critical: false`.

**NT-FR-026:** The quiet hours evaluation SHALL happen before channel dispatching to avoid rendering templates for notifications that will be deferred.

---

### 3.2 Telegram Bot Integration

The Telegram Bot is the P0 (MVP) notification channel, serving as the primary real-time communication channel for trade alerts, fill confirmations, and interactive account management.

#### Bot Registration and Setup

**NT-FR-027:** TrendEdge SHALL operate a single Telegram Bot (created via @BotFather) with the following configuration:
- Bot name: `TrendEdgeBot` (or `TrendEdge_Bot` if taken)
- Description: "AI-powered futures trading alerts, fill confirmations, and account management."
- Commands menu registered with BotFather (see NT-FR-035)
- Bot SHALL run in webhook mode (not polling) in production, receiving updates at `POST /api/integrations/telegram/webhook`
- Bot token SHALL be stored in environment variable `TELEGRAM_BOT_TOKEN`, never committed to source control

**NT-FR-028:** The FastAPI endpoint receiving Telegram webhook updates SHALL verify the request using Telegram's secret token mechanism (X-Telegram-Bot-Api-Secret-Token header) to prevent spoofed requests.

#### User Linking

**NT-FR-029:** User linking SHALL follow this flow:

1. User navigates to Settings > Integrations > Telegram in the TrendEdge dashboard.
2. System generates a 6-character alphanumeric linking code (uppercase, no ambiguous characters I/O/0/1), valid for 10 minutes. Code is stored in Redis with key `telegram_link:{code}` and value `{user_id}`.
3. Dashboard displays: "Send this code to @TrendEdgeBot on Telegram: `{code}`"
4. User opens Telegram, starts conversation with @TrendEdgeBot, sends the code.
5. Bot receives the code, looks up the associated `user_id` in Redis, stores the mapping `telegram_chat_id -> user_id` in the `user_integrations` table.
6. Bot replies: "Your Telegram account has been linked to TrendEdge. You will now receive trade alerts here. Type /help to see available commands."
7. Dashboard updates to show "Telegram: Connected" with the linked Telegram username and a "Disconnect" button.
8. If the code is expired or invalid, the bot replies: "Invalid or expired code. Please generate a new code from your TrendEdge dashboard."

**NT-FR-030:** Each TrendEdge account SHALL be linkable to exactly one Telegram chat. Re-linking replaces the previous association. The previous chat receives a message: "Your Telegram account has been unlinked from TrendEdge. Another Telegram account has been linked."

**NT-FR-031:** Users SHALL be able to disconnect Telegram from the dashboard (Settings > Integrations > Telegram > Disconnect) or by sending `/unlink` to the bot. Both actions delete the `telegram_chat_id` mapping and send a confirmation to the Telegram chat: "Your Telegram account has been unlinked from TrendEdge."

#### Alert Message Formatting

**NT-FR-032:** Telegram messages SHALL use Markdown V2 formatting for structured, readable alerts. Messages SHALL include relevant emoji indicators for quick visual scanning:

| Event | Format |
|---|---|
| Trade Fill (Entry) | Direction arrow + instrument + price + stop/target + risk + R:R + source |
| Trade Fill (Exit) | Close indicator + instrument + P&L (dollars and R-multiple) + duration + daily P&L running total |
| Trendline Alert | Alert type + instrument + grade + touch count + slope + action guidance |
| Daily P&L Summary | Calendar date + net P&L + trade count (W/L) + win rate + equity curve direction + top/bottom trade |
| Risk Warning | Warning indicator + limit type + current vs. max + recommended action |
| Risk Breach | Alert indicator + limit type + auto-action taken (e.g., "Execution paused") |
| Connection Lost | Alert indicator + broker name + timestamp + "Attempting reconnect..." |

**NT-FR-033:** All monetary values in Telegram messages SHALL be formatted with proper comma separation and 2 decimal places (e.g., `$1,250.50`). Tick values SHALL use the instrument's tick size precision.

**NT-FR-034:** Telegram messages for trade events SHALL include an inline keyboard button linking to the trade detail page in the dashboard: `[View Trade Details](https://app.trendedge.com/trades/{trade_id})`.

#### Interactive Commands

**NT-FR-035:** The Telegram Bot SHALL support the following commands:

| Command | Description | Response |
|---|---|---|
| `/start` | Initial bot greeting | Welcome message with linking instructions |
| `/help` | List available commands | Formatted command list with descriptions |
| `/status` | Current account overview | Open positions, unrealized P&L, daily P&L, available margin, execution status (active/paused) |
| `/positions` | Detailed open positions | Table of open positions: symbol, direction, qty, entry price, current price, unrealized P&L, R-multiple |
| `/pnl` | Today's P&L breakdown | Closed trades list with P&L, running total, win/loss count |
| `/pnl week` | This week's P&L | Weekly P&L summary with equity curve (text sparkline) |
| `/pnl month` | This month's P&L | Monthly P&L summary with key metrics |
| `/pause` | Pause automated execution | Confirms pause; all pending signals queued but not executed. Existing positions unaffected. |
| `/resume` | Resume automated execution | Confirms resume; queued signals are discarded (stale). New signals processed normally. |
| `/alerts` | Active trendline alerts | List of active trendline setups being monitored with grades and estimated interaction prices |
| `/unlink` | Disconnect Telegram | Confirmation prompt, then unlinks account |

**NT-FR-036:** The `/status` command SHALL return a response within 3 seconds. If broker data is unavailable, the response SHALL show cached data with a "Data as of {timestamp}" disclaimer.

**NT-FR-037:** The `/pause` command SHALL require confirmation via inline keyboard: "Are you sure you want to pause automated execution? [Yes, Pause] [Cancel]". On confirmation, the system sets `user.execution_paused = true` in the database and sends to all the user's active channels: "Automated execution has been PAUSED. Use /resume to re-enable."

**NT-FR-038:** When execution is paused, all inbound signals (TradingView webhooks, trendline engine alerts) SHALL be logged in `signal_log` with status `paused_skipped` but NOT routed to the execution engine. The user SHALL receive a Telegram notification for each skipped signal: "Signal received but execution is PAUSED: BUY MES @ 5,205.25. Use /resume to re-enable."

#### Manual Trade Entry via Telegram

**NT-FR-039:** The bot SHALL support manual trade entry via the following command syntax:

```
/trade <ACTION> <SYMBOL> <PRICE> SL:<STOP_LOSS> TP:<TAKE_PROFIT> [QTY:<QUANTITY>]
```

Examples:
- `/trade BUY MES 5200 SL:5190 TP:5220` -- Buy 1 MES at 5200 (quantity defaults to 1)
- `/trade SELL CL 72.50 SL:73.25 TP:71.00 QTY:2` -- Sell 2 CL at 72.50

**NT-FR-040:** Before executing a manual trade command, the bot SHALL:
1. Parse and validate all parameters (valid symbol, numeric prices, stop on correct side of entry, target on correct side of entry).
2. Calculate risk amount, R:R ratio, and position size in dollars.
3. Run the standard risk check (daily loss limit, max positions, position size limit).
4. Display a confirmation summary with inline keyboard: "[Confirm & Execute] [Cancel]"
5. On confirmation, route to the execution pipeline as a `manual_telegram` signal source.
6. On successful order placement, reply with the fill confirmation template.

**NT-FR-041:** If any validation or risk check fails, the bot SHALL reply with the specific reason: "Cannot execute: Daily loss limit would be exceeded. Remaining risk budget: $200. This trade risks $500."

---

### 3.3 Discord Webhook Integration

Discord integration provides community-facing trade signal sharing and automated summary posts via outgoing webhooks.

#### Webhook URL Configuration

**NT-FR-042:** Users SHALL configure Discord integration via Settings > Integrations > Discord with the following fields:
- `webhook_url`: Discord webhook URL (validated format: `https://discord.com/api/webhooks/{id}/{token}`)
- `channel_name`: Display name for reference (auto-populated from Discord webhook response if possible)
- `enabled_events`: Multi-select of event types to post (defaults: `trade.fill`, `trade.closed`, `trendline.alert`)
- `include_pnl`: Boolean -- whether to include dollar P&L amounts in public posts (default: `false` for privacy)

**NT-FR-043:** On saving the webhook URL, the system SHALL send a test embed to the Discord channel: "TrendEdge integration active. Trade alerts will appear here." If the test fails, the system SHALL display the error: "Could not send to Discord. Please verify the webhook URL is correct and the channel exists."

**NT-FR-044:** Users SHALL be able to configure up to 3 Discord webhook URLs (e.g., separate channels for alerts, fills, and summaries). Each webhook can have independent event type filtering.

#### Rich Embed Formatting

**NT-FR-045:** Trade event notifications SHALL be sent as Discord rich embeds with the following structure:

```json
{
  "embeds": [{
    "title": "Trade Fill: BUY MES",
    "color": 3066993,
    "fields": [
      { "name": "Direction", "value": "LONG", "inline": true },
      { "name": "Entry", "value": "5,205.25", "inline": true },
      { "name": "Quantity", "value": "2", "inline": true },
      { "name": "Stop Loss", "value": "5,190.00", "inline": true },
      { "name": "Target", "value": "5,225.50", "inline": true },
      { "name": "R:R", "value": "1:2.03", "inline": true },
      { "name": "Source", "value": "Trendline Engine", "inline": true },
      { "name": "Grade", "value": "A+", "inline": true }
    ],
    "footer": { "text": "TrendEdge | 2026-02-11 14:32 ET" },
    "timestamp": "2026-02-11T19:32:05Z"
  }]
}
```

**NT-FR-046:** Embed colors SHALL follow this convention:
- Green (`#2ECC71` / `3066993`): Long entries, winning closes
- Red (`#E74C3C` / `15158332`): Short entries, losing closes
- Gold (`#F1C40F` / `15844367`): Trendline alerts
- Blue (`#3498DB` / `3447003`): Informational (summaries, system status)
- Orange (`#E67E22` / `15105570`): Warnings

**NT-FR-047:** When `include_pnl` is `false`, P&L dollar amounts SHALL be replaced with R-multiple values only (e.g., "+1.82R" instead of "+$370.00 (+1.82R)").

#### Daily/Weekly Summary Posts

**NT-FR-048:** If the user has enabled Discord summaries, the system SHALL post a daily summary embed at 17:30 ET (after CME equity market close) containing:
- Date and session type (RTH / full session)
- Net P&L (R-multiples; dollars only if `include_pnl` is `true`)
- Trade count (wins / losses / breakeven)
- Win rate
- Best and worst trade
- Active trendline alerts count

**NT-FR-049:** Weekly summaries SHALL be posted on Saturday at 10:00 ET containing:
- Week date range
- Net P&L and cumulative equity change
- Total trade count with win rate
- Average R-multiple
- Playbook performance breakdown
- Top trendline setups of the week

---

### 3.4 Email Notifications (SendGrid/Resend)

Email serves as the universal notification channel available to all tiers, handling transactional emails, trade alerts, and periodic digest reports.

#### Transactional Emails

**NT-FR-050:** The system SHALL send the following transactional emails via SendGrid (primary) or Resend (fallback):

| Email | Trigger | Sender | Subject Line Template |
|---|---|---|---|
| Welcome | User registration | noreply@trendedge.com | "Welcome to TrendEdge -- Let's get your first trendline detected" |
| Email Verification | Registration, email change | noreply@trendedge.com | "Verify your email address" |
| Password Reset | Password reset request | security@trendedge.com | "Reset your TrendEdge password" |
| Broker Connected | Broker API connected | noreply@trendedge.com | "Your {broker_name} account is connected" |
| Trade Fill Alert | `trade.fill` event | alerts@trendedge.com | "{direction} {symbol} filled @ {price}" |
| Trade Closed Alert | `trade.closed` event | alerts@trendedge.com | "Trade closed: {symbol} {pnl_direction}{pnl_amount}" |
| Risk Limit Breach | `risk.limit_breach` event | alerts@trendedge.com | "URGENT: {limit_type} limit reached -- execution paused" |
| Subscription Change | Tier upgrade/downgrade | billing@trendedge.com | "Your TrendEdge plan has been updated to {tier}" |

**NT-FR-051:** All transactional emails SHALL be sent within 30 seconds of the triggering event. Password reset and email verification emails SHALL be sent within 10 seconds.

**NT-FR-052:** All emails SHALL include: the TrendEdge logo, a link to the dashboard, an unsubscribe link (for non-security emails), and a footer with the company address (CAN-SPAM compliance).

#### Digest Emails

**NT-FR-053:** Daily P&L digest emails SHALL be generated and sent at 18:00 in the user's local timezone and contain:

| Section | Content |
|---|---|
| Header | Date, account name, subscription tier badge |
| P&L Summary | Net P&L (dollars and R-multiples), trade count, win rate |
| Trade Table | Each trade: symbol, direction, entry/exit, P&L, R-multiple, duration, playbook |
| Equity Curve | Inline chart image (generated via matplotlib or QuickChart API) showing last 30 days equity |
| Trendline Activity | New setups detected, alerts fired, trendlines invalidated |
| Risk Status | Current daily loss usage, max drawdown distance |
| Footer | Link to dashboard, notification preferences link, unsubscribe link |

**NT-FR-054:** Weekly performance digest emails SHALL be sent on Sunday at 09:00 in the user's local timezone and contain:

| Section | Content |
|---|---|
| Week Summary | Date range, net P&L, total trades, win rate, Sharpe ratio (annualized) |
| Playbook Breakdown | Per-playbook: trade count, win rate, avg R, total P&L |
| Best/Worst Trades | Top 3 winners and top 3 losers with details |
| Equity Curve | 90-day equity curve chart with the current week highlighted |
| Behavioral Metrics | Rule compliance rate, mistake cost, consistency score |
| Trendline Report | Active setups, new A+ detections, accuracy rate |
| AI Insight | One-paragraph AI-generated performance observation (Pro tier only) |

**NT-FR-055:** Digest emails SHALL be skipped on days/weeks with zero trading activity. Instead, the system SHALL send a lighter "No activity" email: "No trades were executed on {date}. You have {count} active trendline setups being monitored." This email SHALL be suppressible via preferences.

#### Email Template Management

**NT-FR-056:** Email templates SHALL be built as responsive HTML using MJML (compiled to HTML) and stored in `templates/email/`. Each template SHALL be tested against the following email clients: Gmail (web + mobile), Outlook (desktop + web), Apple Mail.

**NT-FR-057:** Email templates SHALL support the following layout components:
- Header with logo and navigation
- Section containers with alternating backgrounds
- Data tables for trade lists
- Inline chart images (attached as CID or hosted URL)
- Call-to-action buttons (primary and secondary styles)
- Footer with social links, unsubscribe, and legal text

**NT-FR-058:** The system SHALL maintain a template version history. When a template is updated, existing queued emails SHALL use the template version that was current when they were queued, not the updated version.

#### Unsubscribe Handling

**NT-FR-059:** Every non-security email SHALL include a one-click unsubscribe link (compliant with RFC 8058 List-Unsubscribe-Post header). Clicking the link SHALL:
1. Immediately unsubscribe the user from that email category (e.g., daily digest, trade alerts).
2. Display a confirmation page: "You have been unsubscribed from {category} emails. You can re-enable this in your notification preferences." with a link to preferences and an "Undo" button (valid for 7 days).
3. NOT unsubscribe from security-related emails (password reset, email verification, risk limit breaches).

**NT-FR-060:** The system SHALL track unsubscribe events in the `notification_preferences` table and honor them immediately. Re-subscribing requires explicit action in the notification preferences UI.

**NT-FR-061:** SendGrid suppression list integration SHALL be implemented: if SendGrid reports a bounce, spam complaint, or unsubscribe via webhook, the system SHALL update the user's email preferences accordingly and log the event.

---

### 3.5 TradingView Webhook Receiver

The webhook receiver accepts inbound signals from TradingView alerts, validates their authenticity, maps symbols to broker-specific contracts, and routes them to the execution pipeline.

#### Unique URL Generation

**NT-FR-062:** Each user SHALL receive a unique webhook URL upon account creation, following the format:

```
https://api.trendedge.com/webhooks/tv/{user_webhook_id}
```

Where `user_webhook_id` is a URL-safe Base62-encoded UUID (22 characters). This ID is NOT the user's account ID -- it is a separate, revocable identifier.

**NT-FR-063:** Each user SHALL also receive an API key for webhook authentication:
- Format: `te_wh_` prefix + 32-character cryptographically random hex string (e.g., `te_wh_a1b2c3d4e5f6...`)
- Stored as a bcrypt hash in the database; the plaintext is shown once at creation and never again.
- Users can regenerate the API key at any time; the old key is immediately invalidated.

**NT-FR-064:** The webhook URL and API key SHALL be displayed in Settings > Integrations > TradingView with:
- Copy-to-clipboard buttons for both URL and API key
- A sample TradingView alert message JSON that the user can paste directly:

```json
{
  "api_key": "YOUR_API_KEY",
  "ticker": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "price": "{{close}}",
  "quantity": "{{strategy.order.contracts}}",
  "stop_loss": "{{plot_0}}",
  "take_profit": "{{plot_1}}",
  "message": "{{strategy.order.comment}}"
}
```

#### Payload Validation

**NT-FR-065:** The webhook endpoint SHALL validate incoming requests in the following order:

1. **URL validation:** Verify `user_webhook_id` exists and is active. If not: return `404 Not Found` with body `{"error": "unknown_endpoint"}`.

2. **Rate limiting:** Check per-user webhook rate limit (60 requests/hour, burst of 10/minute). If exceeded: return `429 Too Many Requests` with `Retry-After` header.

3. **Content-Type:** Verify `Content-Type: application/json`. If not: return `415 Unsupported Media Type`.

4. **Payload parsing:** Parse JSON body. If malformed: return `400 Bad Request` with body `{"error": "invalid_json"}`.

5. **API key validation:** Extract `api_key` field from payload. Verify against stored bcrypt hash. If missing or invalid: return `401 Unauthorized` with body `{"error": "invalid_api_key"}`.

6. **HMAC signature (optional enhanced security):** If the user has enabled HMAC signing in their settings, verify the `X-TrendEdge-Signature` header containing `HMAC-SHA256(webhook_secret, request_body)`. If invalid: return `401 Unauthorized` with body `{"error": "invalid_signature"}`.

7. **Required fields:** Verify presence of `ticker` and `action` fields. If missing: return `422 Unprocessable Entity` with body `{"error": "missing_required_fields", "fields": ["ticker"]}`.

8. **Action validation:** Verify `action` is one of: `buy`, `sell`, `close`, `close_long`, `close_short` (case-insensitive). If invalid: return `422 Unprocessable Entity` with body `{"error": "invalid_action", "value": "..."}`.

**NT-FR-066:** Successful validation SHALL return `200 OK` with body:
```json
{
  "status": "accepted",
  "signal_id": "sig_abc123def456",
  "message": "Signal accepted and queued for processing"
}
```

**NT-FR-067:** The endpoint SHALL respond within 500ms regardless of processing outcome. Signal processing (risk checks, order construction, execution) SHALL happen asynchronously via the Celery task queue.

#### Symbol Mapping

**NT-FR-068:** The system SHALL maintain a symbol mapping table that translates TradingView ticker symbols to broker-specific contract symbols:

| TradingView Symbol | Instrument | IBKR Symbol | Tradovate Symbol | Contract Type |
|---|---|---|---|---|
| `ES1!` | E-mini S&P 500 | `ES` + expiry | `ESH6` | Front month |
| `MES1!` | Micro E-mini S&P | `MES` + expiry | `MESH6` | Front month |
| `NQ1!` | E-mini Nasdaq 100 | `NQ` + expiry | `NQH6` | Front month |
| `MNQ1!` | Micro E-mini Nasdaq | `MNQ` + expiry | `MNQH6` | Front month |
| `YM1!` | E-mini Dow | `YM` + expiry | `YMH6` | Front month |
| `MYM1!` | Micro E-mini Dow | `MYM` + expiry | `MYMH6` | Front month |
| `CL1!` | Crude Oil | `CL` + expiry | `CLJ6` | Front month |
| `MCL1!` | Micro Crude Oil | `MCL` + expiry | `MCLJ6` | Front month |
| `GC1!` | Gold | `GC` + expiry | `GCJ6` | Front month |
| `MGC1!` | Micro Gold | `MGC` + expiry | `MGCJ6` | Front month |
| `PL1!` | Platinum | `PL` + expiry | `PLJ6` | Front month |
| `SI1!` | Silver | `SI` + expiry | `SIH6` | Front month |

**NT-FR-069:** The symbol mapping SHALL automatically resolve front-month continuous contract references (`ES1!`, `NQ1!`) to the current active contract month based on a rollover calendar. The rollover calendar SHALL be configurable per instrument with default rollover dates set to 1 week before contract expiration.

**NT-FR-070:** Users SHALL be able to define custom symbol mappings in Settings > Integrations > TradingView > Symbol Mappings for non-standard TradingView tickers or custom indicator outputs.

**NT-FR-071:** If a symbol cannot be resolved, the webhook SHALL return `200 OK` (to prevent TradingView from disabling the alert) but log the signal with status `symbol_unmapped` and send a notification to the user: "Webhook received but symbol '{ticker}' could not be mapped. Please add a custom mapping in Settings."

#### Error Response Handling

**NT-FR-072:** All webhook error responses SHALL follow this JSON structure:
```json
{
  "status": "error",
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {}
}
```

**NT-FR-073:** The system SHALL NOT return detailed error information that could aid attackers. Specifically:
- Invalid `user_webhook_id` returns generic `404` (not "user not found")
- Invalid `api_key` returns generic `401` (not "key does not match user X")
- Internal errors return `500` with `{"error": "internal_error"}` (no stack traces)

#### Webhook Activity Log

**NT-FR-074:** Every webhook request SHALL be logged in the `webhook_log` table:

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Resolved user (null if URL invalid) |
| `received_at` | TIMESTAMPTZ | Request received timestamp |
| `source_ip` | INET | Request source IP address |
| `payload` | JSONB | Raw request body (API key redacted) |
| `validation_status` | VARCHAR(20) | `valid`, `invalid_key`, `invalid_payload`, `rate_limited`, `unknown_url` |
| `mapped_symbol` | VARCHAR(20) | Resolved broker symbol (null if unmapped) |
| `signal_id` | UUID | Reference to created signal (null if validation failed) |
| `response_code` | INTEGER | HTTP status code returned |
| `processing_time_ms` | INTEGER | Total request processing time |

**NT-FR-075:** The webhook activity log SHALL be viewable in the dashboard at Settings > Integrations > TradingView > Activity Log, showing the most recent 100 webhooks with filtering by status. Users SHALL see: timestamp, source symbol, mapped symbol, status (color-coded), and resulting signal ID (linked to signal detail).

**NT-FR-076:** Webhook logs SHALL be retained for 30 days. Logs older than 30 days SHALL be purged via a daily Celery Beat task.

---

### 3.6 In-App Notification Center

The in-app notification center provides real-time, persistent notification history within the TrendEdge dashboard.

#### Real-Time Delivery via WebSocket

**NT-FR-077:** In-app notifications SHALL be delivered in real time via Supabase Realtime (PostgreSQL LISTEN/NOTIFY under the hood). When a notification is inserted into the `notifications` table for a user, all active browser sessions for that user SHALL receive the notification within 2 seconds.

**NT-FR-078:** The frontend SHALL subscribe to the Supabase Realtime channel `notifications:{user_id}` on dashboard mount. The subscription SHALL include Row-Level Security filters ensuring users only receive their own notifications.

**NT-FR-079:** When a new notification arrives via WebSocket:
1. The notification bell icon badge count SHALL increment.
2. A toast notification SHALL appear in the bottom-right corner of the screen showing: event icon, title, and first line of the message. The toast SHALL auto-dismiss after 5 seconds.
3. If the notification panel is open, the new notification SHALL prepend to the list with a brief highlight animation.

**NT-FR-080:** If the WebSocket connection is lost, the frontend SHALL:
1. Display a subtle "Reconnecting..." indicator near the notification bell.
2. Attempt reconnection with exponential backoff (1s, 2s, 4s, 8s, max 30s).
3. On reconnection, fetch any missed notifications since the last received timestamp via REST API.

#### Notification History

**NT-FR-081:** The `notifications` table SHALL have the following schema:

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Target user (FK, indexed) |
| `event_type` | VARCHAR(50) | Event type (indexed) |
| `title` | VARCHAR(200) | Short notification title |
| `body` | TEXT | Notification body (Markdown supported) |
| `data` | JSONB | Structured data for deep linking (e.g., `{"trade_id": "..."}`) |
| `read` | BOOLEAN | Read status (default: `false`, indexed) |
| `created_at` | TIMESTAMPTZ | Creation timestamp (indexed) |
| `expires_at` | TIMESTAMPTZ | Optional expiration (null = never) |

**NT-FR-082:** The notification panel SHALL support:
- Infinite scroll pagination (20 notifications per page)
- Filtering by event type (dropdown: All, Trades, Trendlines, Risk, System)
- "Mark all as read" button
- Individual "mark as read" on click
- Swipe-to-dismiss on mobile viewports (marks as read, does not delete)
- "Clear all read" button to remove read notifications from the panel

**NT-FR-083:** Unread notification count SHALL be displayed as a badge on the notification bell icon. The count SHALL be fetched on page load via REST API (`GET /api/notifications/unread-count`) and maintained in real time via WebSocket.

**NT-FR-084:** Clicking a notification with a `data.trade_id` SHALL navigate to the trade detail page. Clicking a notification with a `data.trendline_id` SHALL navigate to the trendline detail view. Other notifications SHALL open the notification panel if not already open.

**NT-FR-085:** In-app notifications SHALL expire and be automatically deleted after 30 days via a daily Celery Beat cleanup task. Critical event notifications (`trade.fill`, `risk.limit_breach`) SHALL be retained for 90 days.

---

### 3.7 Market Data Integration

Market data integrations feed the trendline detection engine, analytics calculations, and real-time dashboard displays.

#### Historical OHLCV Data Fetching (yfinance)

**NT-FR-086:** The system SHALL fetch historical daily OHLCV data via the `yfinance` Python library for the following instruments:

| Instrument | yfinance Ticker | Description |
|---|---|---|
| E-mini S&P 500 | `ES=F` | Front-month continuous |
| Micro E-mini S&P | `MES=F` | Front-month continuous |
| E-mini Nasdaq 100 | `NQ=F` | Front-month continuous |
| Micro E-mini Nasdaq | `MNQ=F` | Front-month continuous |
| E-mini Dow | `YM=F` | Front-month continuous |
| Crude Oil | `CL=F` | Front-month continuous |
| Gold | `GC=F` | Front-month continuous |
| Platinum | `PL=F` | Front-month continuous |
| Silver | `SI=F` | Front-month continuous |

**NT-FR-087:** Historical data fetching SHALL operate on the following schedule:
- **Initial fetch:** On instrument activation, fetch maximum available history (typically 2 years of daily data from yfinance).
- **Daily update:** Celery Beat task at 18:30 ET (after settlement) fetches the latest day's OHLCV and appends to the local database.
- **Backfill:** If gaps are detected (missing dates), the system SHALL automatically backfill from yfinance.

**NT-FR-088:** Fetched data SHALL be stored in a `market_data_daily` table:

| Field | Type | Description |
|---|---|---|
| `id` | BIGSERIAL | Primary key |
| `symbol` | VARCHAR(10) | Normalized symbol (e.g., `ES`) |
| `date` | DATE | Trading date |
| `open` | NUMERIC(12,4) | Open price |
| `high` | NUMERIC(12,4) | High price |
| `low` | NUMERIC(12,4) | Low price |
| `close` | NUMERIC(12,4) | Close (settlement) price |
| `volume` | BIGINT | Total volume |
| `source` | VARCHAR(20) | Data source (`yfinance`, `databento`, `broker`) |
| `fetched_at` | TIMESTAMPTZ | When data was fetched |

Unique constraint on `(symbol, date)`. Index on `(symbol, date DESC)`.

**NT-FR-089:** For higher-quality continuous contract data (adjusted for rollovers), the system SHALL support Nasdaq Data Link as an alternative source, configurable per instrument. Nasdaq Data Link tickers (e.g., `CHRIS/CME_ES1`) provide back-adjusted continuous series.

**NT-FR-090:** For intraday data (4H candles required by the trendline engine), the system SHALL use Databento's API (utilizing the $125 free credit) or construct 4H bars from broker-provided real-time data. yfinance SHALL NOT be used for intraday data due to reliability limitations.

#### Real-Time Data via Broker APIs

**NT-FR-091:** Real-time price data SHALL be sourced from the user's connected broker API:
- **IBKR:** Subscribe to Level 1 market data via `ib_async` for quoted instruments. Provides: bid, ask, last, volume, OHLC bar streaming.
- **Tradovate:** Subscribe to market data via WebSocket. Provides: quotes, DOM (depth of market), time & sales.
- CME real-time data fees ($10-25/month) are passed through to the user via broker subscription.

**NT-FR-092:** Real-time data SHALL be used for:
- Dashboard current price display (updated every 1 second for active instruments)
- Unrealized P&L calculation for open positions
- Trendline proximity alerts (price approaching a qualifying trendline)
- MAE/MFE tracking for open trades

**NT-FR-093:** If a user does not have a broker connected (or the connection is down), the system SHALL fall back to delayed data (15-minute delay) sourced from yfinance or the most recent cached price, with a clear "Delayed" indicator in the UI.

#### Data Caching and Refresh Strategy

**NT-FR-094:** Market data SHALL be cached at multiple levels:

| Cache Layer | Technology | TTL | Data |
|---|---|---|---|
| Hot cache | Redis | 5 seconds | Current bid/ask/last for subscribed instruments |
| Warm cache | Redis | 5 minutes | Recent 4H bars, daily bars, computed indicators |
| Cold cache | PostgreSQL | Permanent | Full historical daily OHLCV, archived 4H data |

**NT-FR-095:** The trendline engine SHALL read from the warm cache for scheduled scans (every 4H) and from cold cache for backtesting/historical analysis. It SHALL NOT make direct API calls to data sources during scan execution.

**NT-FR-096:** Cache invalidation SHALL follow these rules:
- Hot cache: overwritten on every new tick/quote from broker
- Warm cache: rebuilt on each new 4H bar close or daily settlement
- Cold cache: append-only; only updated by the daily data fetch job

#### Continuous Contract Symbol Resolution

**NT-FR-097:** The system SHALL maintain a `contract_calendar` table mapping instruments to their expiration schedule:

| Field | Type | Description |
|---|---|---|
| `symbol` | VARCHAR(10) | Base instrument symbol (e.g., `ES`) |
| `contract_month` | CHAR(5) | Contract code (e.g., `ESH26` for March 2026) |
| `first_trade_date` | DATE | First trading date of the contract |
| `last_trade_date` | DATE | Last trading date / expiration |
| `rollover_date` | DATE | Recommended rollover date (default: 7 days before expiration) |
| `is_active` | BOOLEAN | Whether this is the current front-month contract |

**NT-FR-098:** The system SHALL automatically update the `is_active` flag when the rollover date is reached, transitioning the front month from the expiring contract to the next contract. A notification SHALL be sent to affected users: "Contract rollover: {symbol} rolled from {old_contract} to {new_contract}. Active positions in the old contract are unaffected."

**NT-FR-099:** Symbol resolution SHALL be performed by a `SymbolResolver` service that accepts any of: TradingView continuous (`ES1!`), yfinance continuous (`ES=F`), specific contract (`ESH26`), or base symbol (`ES`) and returns the correct broker-specific contract symbol for the user's connected broker.

---

### 3.8 Notification Preferences Management UI

**NT-FR-100:** The notification preferences page SHALL be accessible at Settings > Notifications and contain the following sections:

#### Channel Configuration

**NT-FR-101:** The top section SHALL display each notification channel as a card:

| Channel | Status States | Configuration Fields |
|---|---|---|
| Email | Always available | Email address (from account), verified status |
| In-App | Always available | No configuration needed |
| Telegram | Requires linking | Linked status, Telegram username, link/unlink button |
| Discord | Requires webhook URL | Webhook URL input, channel name, test button |
| Custom Webhook (Team) | Requires URL + auth | URL, auth header, test button |

Each channel card SHALL show the tier requirement if the user's current tier does not include it, with an upgrade CTA.

#### Per-Event Preferences Matrix

**NT-FR-102:** Below the channel cards, a matrix table SHALL allow users to toggle which events go to which channels:

| Event | Email | In-App | Telegram | Discord |
|---|---|---|---|---|
| Trade Fill (Entry) | toggle | toggle | toggle | toggle |
| Trade Fill (Exit) | toggle | toggle | toggle | toggle |
| Trade Closed (P&L) | toggle | toggle | toggle | toggle |
| Trendline Alert | toggle | toggle | toggle | toggle |
| Trendline Invalidated | toggle | toggle | toggle | toggle |
| Risk Warning | toggle | toggle | toggle | toggle |
| Risk Breach | ON (locked) | ON (locked) | toggle | toggle |
| Daily P&L Digest | toggle | -- | toggle | toggle |
| Weekly Digest | toggle | -- | -- | toggle |
| Webhook Errors | toggle | toggle | toggle | -- |
| Connection Lost | ON (locked) | ON (locked) | toggle | -- |
| System Maintenance | toggle | toggle | -- | -- |

**NT-FR-103:** Risk breach and connection lost events SHALL have email and in-app toggles locked to ON (always sent). These cannot be disabled by the user.

**NT-FR-104:** Channels unavailable on the user's tier SHALL have their column grayed out with a lock icon. Hovering over a locked toggle SHALL show a tooltip: "Available on {tier_name} plan."

#### Quiet Hours Configuration

**NT-FR-105:** A dedicated "Quiet Hours" card SHALL allow configuration of:
- Enable/disable toggle
- Start time picker (HH:MM)
- End time picker (HH:MM)
- Timezone selector (populated from IANA timezone database, defaulting to user's account timezone)
- Day-of-week checkboxes (default: all days)
- "Allow critical alerts during quiet hours" checkbox (default: checked)

#### Digest Schedule Configuration

**NT-FR-106:** A "Digest Schedule" card SHALL allow:
- Daily digest: enable/disable, delivery time (default: 18:00 user timezone), skip if no trades (checkbox)
- Weekly digest: enable/disable, delivery day (default: Sunday), delivery time (default: 09:00 user timezone)

#### Preferences Persistence

**NT-FR-107:** Notification preferences SHALL be stored in a `notification_preferences` JSONB column on the `users` table (or a dedicated `notification_preferences` table if the JSON structure exceeds 50 fields). Changes SHALL be saved immediately on toggle (optimistic UI with rollback on error), not requiring a "Save" button.

**NT-FR-108:** Default preferences for new users SHALL be:

| Event | Email | In-App | Telegram | Discord |
|---|---|---|---|---|
| Trade fills | ON | ON | ON | OFF |
| Trade closed | ON | ON | ON | ON |
| Trendline alerts | OFF | ON | ON | OFF |
| Risk warnings | ON | ON | ON | OFF |
| Risk breaches | ON | ON | ON | ON |
| Daily digest | ON | -- | ON | OFF |
| Weekly digest | ON | -- | OFF | OFF |
| Webhook errors | ON | ON | OFF | -- |
| Connection lost | ON | ON | ON | -- |

---

## 4. Non-Functional Requirements

### Performance

**NT-NFR-001:** Telegram message delivery latency SHALL be less than 5 seconds from event emission to message arrival in the user's Telegram chat (p95). Measured from the timestamp the domain event is published to Redis Pub/Sub to the Telegram API response confirming message delivery.

**NT-NFR-002:** Email delivery latency SHALL be less than 30 seconds from event emission to email accepted by SendGrid/Resend API (p95). Note: actual inbox delivery depends on recipient's email provider and is outside TrendEdge's control.

**NT-NFR-003:** In-app notification delivery latency SHALL be less than 2 seconds from event emission to WebSocket message received by the browser client (p95).

**NT-NFR-004:** Discord webhook delivery latency SHALL be less than 5 seconds from event emission to Discord API response (p95).

**NT-NFR-005:** TradingView webhook endpoint response time SHALL be less than 500ms (p99). The endpoint SHALL return a response before any downstream processing begins.

**NT-NFR-006:** The notification engine SHALL process a minimum of 100 concurrent notification dispatches without degradation (to support simultaneous events during high-volume market periods).

### Reliability

**NT-NFR-007:** Critical notification delivery rate SHALL be 99.9% or higher, measured monthly. Critical events: `trade.fill`, `trade.rejected`, `risk.limit_breach`, `account.connection_lost`. A notification is "delivered" when at least one channel confirms receipt.

**NT-NFR-008:** The notification engine SHALL survive individual channel outages without affecting other channels. A Telegram API outage SHALL NOT delay email or in-app notifications.

**NT-NFR-009:** The webhook receiver SHALL maintain 99.95% uptime, measured monthly. Downtime is defined as the endpoint returning 5xx errors or failing to respond within 5 seconds.

**NT-NFR-010:** Notification data (logs, preferences, templates) SHALL be backed up daily as part of the PostgreSQL backup strategy defined in PRD-001.

### Scalability

**NT-NFR-011:** The notification engine SHALL scale horizontally by adding Celery workers. The system SHALL support up to 1,000 concurrent users with notification preferences without architectural changes.

**NT-NFR-012:** The webhook receiver SHALL handle up to 100 requests/second sustained (supporting 1,000+ users with active TradingView alerts firing simultaneously during volatile market events).

**NT-NFR-013:** In-app notification storage SHALL support up to 10,000 notifications per user (with the 30/90-day retention policy keeping this in check).

### Observability

**NT-NFR-014:** The following metrics SHALL be collected and reported to the monitoring system (Sentry + Axiom):
- Notification dispatch latency per channel (histogram)
- Notification delivery success/failure rate per channel (counter)
- Webhook request rate, validation failure rate, processing time (histogram)
- Active WebSocket connections count (gauge)
- Channel circuit breaker activations (counter)
- Rate limit hits per channel (counter)
- Celery notification queue depth (gauge)

**NT-NFR-015:** Alerts SHALL be configured for:
- Notification queue depth > 500 for more than 2 minutes
- Channel failure rate > 5% over a 5-minute window
- Webhook validation failure rate > 20% over a 10-minute window (potential attack)
- Circuit breaker activation (immediate alert)

---

## 5. Dependencies

### Internal PRD Dependencies

| PRD | Dependency | What This PRD Needs |
|---|---|---|
| PRD-001: Infrastructure & DevOps | Hard | PostgreSQL database, Redis cache, Celery workers, environment variable management, monitoring (Sentry/Axiom), CI/CD pipeline, Supabase Realtime setup |
| PRD-003: Trade Execution Engine | Hard | Domain events for `trade.fill`, `trade.rejected`, `trade.closed`; execution pause/resume API; signal ingestion API for TradingView webhooks; bracket order construction for manual Telegram trades |
| PRD-008: Authentication & Authorization | Hard | User identity, subscription tier resolution, API key management, session management for WebSocket auth, RLS policies for notification data isolation |
| PRD-002: Trendline Detection Engine | Medium | Domain events for `trendline.alert`, `trendline.invalidated`; trendline metadata for notification templates |
| PRD-004: Trade Journaling | Medium | Trade detail page URLs for notification deep links; journal entry creation trigger for manual Telegram trades |
| PRD-005: Analytics & Performance | Medium | Daily/weekly P&L data for digest emails; playbook performance data for weekly summaries |
| PRD-006: Risk Management | Medium | Domain events for `risk.limit_breach`, `risk.warning`; risk limit data for notification templates |
| PRD-009: Billing & Subscriptions | Medium | Subscription tier for channel gating; `subscription.changed` event for notification preference updates |

### External Service Dependencies

| Service | Purpose | Failure Impact | Fallback |
|---|---|---|---|
| Telegram Bot API | Telegram message delivery | Telegram notifications delayed/failed | Retry with backoff; fallback to email + in-app |
| Discord Webhook API | Discord embed delivery | Discord posts delayed/failed | Retry with backoff; no fallback (non-critical) |
| SendGrid API | Transactional + digest email delivery | Email delayed/failed | Resend API as secondary provider; in-app fallback for critical |
| Resend API | Backup email provider | N/A (fallback only) | SendGrid is primary |
| Supabase Realtime | WebSocket notification delivery | In-app notifications delayed | REST polling fallback (every 30s) |
| yfinance | Historical OHLCV data | Data fetching fails | Cached data remains valid; alert user; retry next cycle |
| Databento API | Intraday data (4H bars) | Intraday data gaps | Construct from broker real-time data; fall back to daily only |
| Nasdaq Data Link | Continuous contract data | Historical data gaps | yfinance as fallback; manual data entry |
| IBKR TWS API | Real-time market data + execution | Real-time data unavailable | Delayed data from yfinance; execution blocked with user notification |
| Tradovate WebSocket API | Real-time market data + execution | Real-time data unavailable | Same as IBKR fallback |

---

## 6. Testing Requirements

### Channel Delivery Testing

**NT-TR-001:** Unit tests SHALL mock all external channel APIs (Telegram, Discord, SendGrid) and verify:
- Correct template rendering for each event type per channel
- Correct HTTP request construction (headers, body, auth)
- Correct handling of API success responses
- Correct handling of API error responses (rate limit, auth failure, server error)
- Retry task scheduling on failure

**NT-TR-002:** Integration tests SHALL use sandbox/test environments for each channel:
- Telegram: Test bot with a dedicated test chat (not production bot)
- Discord: Test webhook URL pointing to a test server
- SendGrid: Sandbox mode (`mail.send` with `sandbox_mode: true`)
- Email visual testing: Send to Litmus or Email on Acid for rendering verification

**NT-TR-003:** End-to-end delivery tests SHALL verify the full pipeline from event emission to channel delivery for each event type, measuring latency against NFR targets.

### Webhook Validation Testing

**NT-TR-004:** Webhook validation tests SHALL cover:

| Test Case | Input | Expected Result |
|---|---|---|
| Valid payload with correct API key | Well-formed JSON, valid key | `200 OK`, signal created |
| Missing API key | JSON without `api_key` field | `401 Unauthorized` |
| Invalid API key | JSON with wrong `api_key` | `401 Unauthorized` |
| Malformed JSON | Non-JSON body | `400 Bad Request` |
| Missing required fields | JSON without `ticker` | `422 Unprocessable Entity` |
| Invalid action value | `action: "short"` | `422 Unprocessable Entity` |
| Invalid webhook URL | Non-existent `user_webhook_id` | `404 Not Found` |
| Rate limited | 61st request in 1 hour | `429 Too Many Requests` |
| Valid HMAC signature | Correct signature header | `200 OK` |
| Invalid HMAC signature | Wrong signature header | `401 Unauthorized` |
| Unknown symbol | `ticker: "INVALID1!"` | `200 OK`, signal logged as `symbol_unmapped` |
| Oversized payload | Body > 10KB | `413 Payload Too Large` |
| Replay attack | Duplicate `correlation_id` within 5 minutes | `409 Conflict` |

**NT-TR-005:** Fuzz testing SHALL be performed on the webhook endpoint with randomized payloads to verify the endpoint never returns 5xx errors or leaks information.

### Rate Limiting Verification

**NT-TR-006:** Rate limiting tests SHALL verify:
- Notifications are throttled correctly at the per-user per-channel limits defined in NT-FR-020.
- Critical events bypass rate limits.
- Rate limit counters reset correctly after the window expires.
- Batching of throttled notifications produces a correct summary message.
- Redis sliding window counters handle edge cases (counter expiry, Redis restart).

### Template Rendering Testing

**NT-TR-007:** Template rendering tests SHALL verify:
- Every event type has a template for every supported channel.
- Templates render correctly with complete event payloads.
- Templates render gracefully with partial payloads (missing optional fields).
- Monetary values format correctly (commas, decimals, currency symbol).
- Timestamps render in the user's configured timezone.
- Telegram Markdown V2 special characters are properly escaped.
- Discord embed field counts do not exceed Discord's limit of 25.
- Email HTML renders without broken images or layout issues.

### Retry Logic Testing

**NT-TR-008:** Retry logic tests SHALL verify:
- Failed deliveries are retried at the correct backoff intervals.
- The retry count increments correctly.
- After max retries, the notification is marked `failed`.
- For Critical events, fallback channel delivery is triggered after max retries.
- Circuit breaker activates after the configured failure threshold.
- Circuit breaker automatically resets after the cooldown period.
- Concurrent retries do not create duplicate notifications.

### Symbol Mapping Accuracy

**NT-TR-009:** Symbol mapping tests SHALL verify:
- All standard TradingView continuous contract symbols map to correct broker symbols.
- Front-month resolution returns the correct contract for the current date.
- Rollover transitions update the active contract correctly.
- Custom user symbol mappings override default mappings.
- Unknown symbols are handled gracefully (logged, user notified, not rejected).

**NT-TR-010:** A monthly automated test SHALL run against live TradingView and broker APIs to verify that symbol mappings remain accurate after contract rollovers.

### Market Data Testing

**NT-TR-011:** Market data integration tests SHALL verify:
- yfinance data fetching returns valid OHLCV data for all configured instruments.
- Data gaps are detected and backfilled automatically.
- Duplicate data points are handled idempotently (upsert, not duplicate insert).
- Cache layers return correct data at each TTL boundary.
- Real-time data subscriptions handle broker disconnection and reconnection.

---

## 7. Security

### Webhook Security

**NT-SEC-001:** Webhook endpoint URLs SHALL use HTTPS exclusively. HTTP requests SHALL be rejected with `301 Moved Permanently` redirecting to the HTTPS equivalent.

**NT-SEC-002:** Webhook API keys SHALL be:
- Generated using `secrets.token_hex(32)` (256 bits of entropy).
- Stored as bcrypt hashes (`cost=12`) in the database; never stored in plaintext.
- Transmitted to the user exactly once at creation, over HTTPS, and never retrievable again.
- Rotatable: users can generate a new key, instantly invalidating the old one.

**NT-SEC-003:** Optional HMAC signature verification SHALL use HMAC-SHA256 with a per-user webhook secret (separate from the API key). The signature SHALL cover the entire request body to prevent tampering.

**NT-SEC-004:** The webhook endpoint SHALL implement IP-based rate limiting (in addition to per-user rate limiting) to mitigate brute-force attacks: 100 requests/minute per source IP. Exceeding this limit SHALL result in a temporary 15-minute block with a `429` response.

**NT-SEC-005:** Webhook payloads SHALL be size-limited to 10KB. Payloads exceeding this limit SHALL be rejected with `413 Payload Too Large`.

### Bot Token Security

**NT-SEC-006:** The Telegram Bot token SHALL be stored exclusively in environment variables (`TELEGRAM_BOT_TOKEN`), never in source code, configuration files, or database records.

**NT-SEC-007:** The Telegram webhook endpoint SHALL verify the `X-Telegram-Bot-Api-Secret-Token` header on every request. Requests without a valid secret token SHALL be silently dropped (no error response to avoid information leakage).

**NT-SEC-008:** Telegram linking codes SHALL be single-use, time-limited (10 minutes), and stored in Redis with automatic expiry. Codes SHALL be invalidated immediately after use or expiry.

### API Key Management

**NT-SEC-009:** All external service API keys (SendGrid, Resend, Databento, Nasdaq Data Link) SHALL be stored in environment variables and managed via the infrastructure's secret management system (defined in PRD-001).

**NT-SEC-010:** API keys SHALL be rotated on the following schedule:
- Webhook API keys: user-initiated rotation at any time
- External service API keys: quarterly, or immediately on suspected compromise
- Telegram Bot token: only on suspected compromise (requires re-registering webhook URL)

**NT-SEC-011:** All API keys in log output SHALL be redacted. The webhook activity log SHALL store payloads with the `api_key` field replaced with `"[REDACTED]"`.

### Data Privacy

**NT-SEC-012:** Notification content SHALL NOT include full account balances or sensitive financial data. P&L values are acceptable as they relate to specific trades, not account totals.

**NT-SEC-013:** Discord webhook posts SHALL respect the user's `include_pnl` privacy setting (NT-FR-047). Dollar amounts SHALL never be posted to public Discord channels without explicit user opt-in.

**NT-SEC-014:** Email notification content SHALL be minimized in subject lines (no P&L amounts in subjects, as subjects are often previewed in notifications on shared devices). Full details SHALL be in the email body.

**NT-SEC-015:** Webhook log entries SHALL not store raw API keys. The `payload` field in `webhook_log` SHALL have the `api_key` value replaced with `"[REDACTED]"` before persistence.

---

## 8. Phase Mapping

### Phase 1: Core Notifications + TradingView Webhook (Weeks 1-2 of Sprint)

**Goal:** Functional Telegram notifications for trade events and a working TradingView webhook receiver. This is the minimum viable notification system for personal trading use.

| Component | Deliverables |
|---|---|
| Notification Engine | Event bus (Redis Pub/Sub), channel dispatch with Telegram adapter, basic retry logic (3 attempts), notification_log table |
| Telegram Bot | Bot registration, user linking flow, trade fill/close templates, `/status`, `/positions`, `/pnl`, `/pause`, `/resume` commands |
| TradingView Webhook | Webhook URL generation, API key validation, symbol mapping table (10 core futures), signal routing to execution pipeline, webhook_log table |
| Market Data | yfinance daily OHLCV fetcher, market_data_daily table, basic Redis caching |
| Preferences | Hardcoded defaults (Telegram ON for all events), no UI yet |

**Acceptance Criteria (Phase 1):**
- [ ] Trade fill on IBKR paper account triggers Telegram message within 5 seconds.
- [ ] TradingView alert with valid API key creates a signal in the execution pipeline within 2 seconds.
- [ ] TradingView alert with invalid API key returns 401 and does not create a signal.
- [ ] `/status` command returns current positions and daily P&L.
- [ ] `/pause` halts execution; `/resume` re-enables it.
- [ ] yfinance fetches daily data for ES, NQ, CL, GC, PL without errors.
- [ ] Symbol mapping resolves `ES1!` to the correct IBKR/Tradovate contract.

### Phase 2: Email Digests + Discord + In-App + Preferences UI (Weeks 3-6)

**Goal:** Full multi-channel notification support with user-configurable preferences, digest emails, and in-app notification center.

| Component | Deliverables |
|---|---|
| Email (SendGrid) | Transactional email templates (welcome, password reset, trade alerts), daily P&L digest, weekly performance digest, unsubscribe handling |
| Discord | Webhook URL configuration, rich embed formatting, daily/weekly summary posts |
| In-App | Supabase Realtime WebSocket delivery, notification panel with history, read/unread tracking, bell icon with badge |
| Notification Engine | Full retry logic (5 attempts with backoff), rate limiting, circuit breaker, quiet hours |
| Preferences UI | Channel configuration cards, per-event preference matrix, quiet hours settings, digest schedule configuration |
| Market Data | Databento/broker intraday data (4H bars), continuous contract rollover calendar, warm cache layer |
| Telegram (enhanced) | Manual trade entry (`/trade`), daily P&L digest scheduled message, `/alerts` command |

**Acceptance Criteria (Phase 2):**
- [ ] Daily P&L digest email arrives at 18:00 user timezone with correct trade data and equity curve chart.
- [ ] Weekly digest email arrives on Sunday with playbook breakdown and behavioral metrics.
- [ ] Discord embed posts to configured webhook with correct formatting and color coding.
- [ ] In-app notifications appear within 2 seconds of event via WebSocket.
- [ ] Notification preference toggles persist immediately and take effect on the next event.
- [ ] Quiet hours defer non-critical notifications and deliver a batch summary when quiet hours end.
- [ ] Rate limiting prevents more than 20 Telegram messages per hour per user.
- [ ] Unsubscribe link in email immediately stops that email category.
- [ ] `/trade BUY MES 5200 SL:5190 TP:5220` creates a valid order after confirmation.

### Phase 3: Tier-Gated Channels + Custom Webhooks + Sentiment (Weeks 7-10)

**Goal:** Enforce subscription tier channel access, add Team-tier custom webhooks, and integrate sentiment data pipeline.

| Component | Deliverables |
|---|---|
| Tier Gating | Channel availability enforced by subscription tier, upgrade prompts in UI, automatic channel disabling on downgrade |
| Custom Webhooks (Team) | Custom webhook URL + auth header configuration, configurable payload format (JSON templates), delivery tracking |
| Sentiment Pipeline | FinBERT daily headline processing, Claude API batch sentiment scoring (Pro tier), sentiment score storage and API exposure |
| Market Data (enhanced) | Nasdaq Data Link continuous contract data, automated rollover detection, data quality monitoring |
| Advanced Telegram | Interactive inline keyboards on fill notifications (Move Stop to BE, Close Position) |

**Acceptance Criteria (Phase 3):**
- [ ] Free-tier user sees Telegram channel locked with upgrade CTA; cannot enable it.
- [ ] Trader-tier user can enable Telegram and Email but not Discord.
- [ ] Pro-tier user can enable all channels.
- [ ] Team-tier user can configure custom webhook URLs and receives notifications via them.
- [ ] Downgrading from Pro to Trader automatically disables Discord with an email notification.
- [ ] Daily sentiment scores are available for configured instruments by 08:00 ET.
- [ ] Inline keyboard "Move Stop to BE" on Telegram fill notification correctly updates the stop order via broker API.

---

## 9. Acceptance Criteria

### System-Level Acceptance Criteria

The notification and integrations system is considered complete and production-ready when ALL of the following criteria are met:

#### Notification Engine

- [ ] AC-NT-001: Every domain event listed in NT-FR-001 triggers the correct notification(s) to the correct channel(s) based on user preferences and tier.
- [ ] AC-NT-002: Critical notifications (`trade.fill`, `risk.limit_breach`, `account.connection_lost`) achieve 99.9% delivery rate over a 30-day measurement period.
- [ ] AC-NT-003: Non-critical notification failures do not impact critical notification delivery (channel isolation verified).
- [ ] AC-NT-004: Retry logic exhausts all 5 attempts with correct backoff timing before marking a notification as failed.
- [ ] AC-NT-005: Fallback channel delivery activates for critical events when the primary channel fails all retries.
- [ ] AC-NT-006: Rate limiting correctly throttles per the defined limits; critical events bypass rate limits.
- [ ] AC-NT-007: Quiet hours defer notifications and deliver a correct batch summary on quiet hours end.
- [ ] AC-NT-008: Circuit breaker activates on sustained channel failure and auto-resets after cooldown.

#### Telegram Bot

- [ ] AC-NT-009: User can link and unlink Telegram account through both dashboard and bot commands.
- [ ] AC-NT-010: All 10 bot commands return correct, well-formatted responses within 3 seconds.
- [ ] AC-NT-011: Trade fill notifications arrive in Telegram within 5 seconds of the fill event.
- [ ] AC-NT-012: `/pause` prevents execution of new signals; `/resume` re-enables execution; existing positions are unaffected.
- [ ] AC-NT-013: Manual trade entry via `/trade` correctly validates inputs, shows confirmation, and routes to execution pipeline.

#### Discord Integration

- [ ] AC-NT-014: Rich embeds display correctly in Discord with proper color coding, field layout, and footer.
- [ ] AC-NT-015: Daily summary posts at 17:30 ET with accurate data from the day's trading activity.
- [ ] AC-NT-016: `include_pnl: false` setting correctly hides dollar amounts from all Discord posts.

#### Email

- [ ] AC-NT-017: Transactional emails (welcome, password reset, trade alerts) deliver within 30 seconds.
- [ ] AC-NT-018: Daily digest email contains accurate trade table, equity curve chart, and risk status for the correct day.
- [ ] AC-NT-019: Weekly digest email contains accurate playbook breakdown and behavioral metrics for the correct week.
- [ ] AC-NT-020: Unsubscribe link immediately stops the specific email category without affecting other categories or security emails.
- [ ] AC-NT-021: Email renders correctly in Gmail, Outlook, and Apple Mail (no broken layouts or missing images).

#### TradingView Webhook

- [ ] AC-NT-022: Valid webhook with correct API key creates a signal and returns `200 OK` within 500ms.
- [ ] AC-NT-023: Invalid API key returns `401` without leaking information.
- [ ] AC-NT-024: Symbol mapping correctly resolves all 12+ standard TradingView continuous contract symbols to current broker contracts.
- [ ] AC-NT-025: Unmapped symbols are handled gracefully: `200 OK` response, user notified, signal logged as `symbol_unmapped`.
- [ ] AC-NT-026: Webhook activity log shows all received webhooks with correct status and is viewable in the dashboard.
- [ ] AC-NT-027: Regenerating webhook URL/API key immediately invalidates the old credentials.

#### In-App Notifications

- [ ] AC-NT-028: Notifications appear in the browser within 2 seconds of event emission via WebSocket.
- [ ] AC-NT-029: Notification bell badge count is accurate and updates in real time.
- [ ] AC-NT-030: Notification panel supports infinite scroll, filtering, mark-as-read, and mark-all-as-read.
- [ ] AC-NT-031: WebSocket reconnection after disconnection fetches missed notifications.

#### Market Data

- [ ] AC-NT-032: yfinance daily data is fetched and stored correctly for all configured instruments by 18:30 ET daily.
- [ ] AC-NT-033: Data gaps are detected and backfilled automatically within 24 hours.
- [ ] AC-NT-034: Real-time broker data updates the dashboard within 1 second of the price change.
- [ ] AC-NT-035: Contract rollover transitions update the active front-month contract without manual intervention.
- [ ] AC-NT-036: Cache layers serve correct data at all TTL boundaries; stale data is never served past its TTL.

#### Tier Gating

- [ ] AC-NT-037: Each subscription tier has access to exactly the channels defined in NT-FR-005; no more, no less.
- [ ] AC-NT-038: Tier downgrade disables unavailable channels and notifies the user via email.
- [ ] AC-NT-039: Tier upgrade immediately enables newly available channels with default preferences.

#### Security

- [ ] AC-NT-040: No API keys, bot tokens, or secrets appear in application logs, error messages, or client-side code.
- [ ] AC-NT-041: Webhook endpoint withstands 1,000 invalid requests without exposing internal information or degrading service.
- [ ] AC-NT-042: Telegram linking codes expire after 10 minutes and are single-use.
- [ ] AC-NT-043: Webhook activity log payloads have API keys redacted.

---

## Appendix

### A. Database Schema Summary

| Table | Purpose | Estimated Rows (1K Users) |
|---|---|---|
| `notification_preferences` | Per-user channel and event preferences | 1,000 |
| `notification_log` | Delivery attempt tracking | ~500K/month |
| `notifications` | In-app notification history | ~100K active |
| `webhook_log` | TradingView webhook request log | ~50K/month |
| `user_integrations` | Telegram, Discord, custom webhook configs | 1,000 |
| `market_data_daily` | Historical OHLCV | ~50K (2yr x 10 instruments x 252 days) |
| `market_data_intraday` | 4H bars | ~200K |
| `contract_calendar` | Futures contract expiration schedule | ~500 |
| `symbol_mappings` | TradingView to broker symbol mapping | ~100 |

### B. Event Payload Examples

**trade.fill event:**
```json
{
  "event_type": "trade.fill",
  "user_id": "usr_abc123",
  "timestamp": "2026-02-11T19:32:05Z",
  "correlation_id": "cor_def456",
  "payload": {
    "trade_id": "trd_ghi789",
    "signal_id": "sig_jkl012",
    "symbol": "MES",
    "contract": "MESH26",
    "direction": "BUY",
    "quantity": 2,
    "fill_price": 5205.25,
    "stop_loss": 5190.00,
    "take_profit": 5225.50,
    "risk_amount": 305.00,
    "rr_ratio": 2.03,
    "slippage_ticks": 0.5,
    "signal_source": "tradingview_webhook",
    "playbook": "A+ Trendline Break",
    "trendline_grade": "A+",
    "trendline_touches": 4
  }
}
```

**digest.daily event:**
```json
{
  "event_type": "digest.daily",
  "user_id": "usr_abc123",
  "timestamp": "2026-02-11T23:00:00Z",
  "correlation_id": "cor_mno345",
  "payload": {
    "date": "2026-02-11",
    "net_pnl": 425.00,
    "net_r": 3.42,
    "trades_count": 4,
    "wins": 3,
    "losses": 1,
    "win_rate": 0.75,
    "best_trade": { "symbol": "MES", "pnl": 370.00, "r": 1.82 },
    "worst_trade": { "symbol": "CL", "pnl": -125.00, "r": -0.65 },
    "active_alerts": 7,
    "daily_loss_used_pct": 0.32
  }
}
```

### C. Telegram Command Quick Reference

```
/start    - Welcome and linking instructions
/help     - Show all available commands
/status   - Account overview (positions, P&L, margin)
/positions - Detailed open positions table
/pnl      - Today's P&L breakdown
/pnl week - This week's P&L summary
/pnl month - This month's P&L summary
/pause    - Pause automated execution
/resume   - Resume automated execution
/alerts   - Active trendline alerts
/trade    - Manual trade entry
/unlink   - Disconnect Telegram account
```

### D. Symbol Mapping Quick Reference

| TradingView | yfinance | Base | IBKR | Tradovate (Mar 2026) |
|---|---|---|---|---|
| `ES1!` | `ES=F` | ES | ES + expiry | ESH6 |
| `MES1!` | `MES=F` | MES | MES + expiry | MESH6 |
| `NQ1!` | `NQ=F` | NQ | NQ + expiry | NQH6 |
| `MNQ1!` | `MNQ=F` | MNQ | MNQ + expiry | MNQH6 |
| `YM1!` | `YM=F` | YM | YM + expiry | YMH6 |
| `CL1!` | `CL=F` | CL | CL + expiry | CLJ6 |
| `GC1!` | `GC=F` | GC | GC + expiry | GCJ6 |
| `PL1!` | `PL=F` | PL | PL + expiry | PLJ6 |
| `SI1!` | `SI=F` | SI | SI + expiry | SIH6 |

### E. Related Documents

- PRD-001: Infrastructure & DevOps
- PRD-002: Trendline Detection Engine
- PRD-003: Trade Execution Engine
- PRD-004: Trade Journaling
- PRD-005: Analytics & Performance
- PRD-006: Risk Management
- PRD-008: Authentication & Authorization
- PRD-009: Billing & Subscriptions
- [TrendEdge Master PRD v1](../TrendEdge%20PRD%20v1.md)
