# PRD-012: Completion Sweep

**TrendEdge -- AI-Powered Futures Trading Platform**

| Field | Value |
|---|---|
| PRD ID | PRD-012 |
| Title | Completion Sweep |
| Version | 1.0 |
| Status | Draft |
| Author | TrendEdge Engineering |
| Created | 2026-02-12 |
| Last Updated | 2026-02-12 |
| Classification | CONFIDENTIAL |

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Dependencies](#5-dependencies)
6. [Testing Requirements](#6-testing-requirements)
7. [Acceptance Criteria](#7-acceptance-criteria)
8. [Phase Mapping](#8-phase-mapping)
9. [Cross-References to Other PRDs](#9-cross-references-to-other-prds)

---

## 1. Overview & Purpose

### 1.1 What This PRD Covers

This PRD addresses residual incomplete items from earlier phases that will not be naturally completed by future phase work. These are standalone deliverables that fell through gaps between PRDs -- either because they are external service configurations, deferred P2 items, or UI features whose parent PRDs are otherwise complete.

Specifically, this document covers four items, each mapped to its own sub-FSD for implementation:

| Sub-Phase | Sub-FSD | Domain | Parent PRD/FSD | Remaining |
|-----------|---------|--------|----------------|-----------|
| CS-1 | FSD-012a | Observability Setup | PRD-001 | ~5% |
| CS-2 | FSD-012b | Account Deletion | PRD-008 | ~15% |
| CS-3 | FSD-012c | Command Palette | FSD-011a | ~50% |
| CS-4 | FSD-012d | IBKR Live Data Feed | PRD-002 | ~2% |

1. **Axiom log shipping and Uptime Robot monitoring** (CS-1 / FSD-012a, ~5% remaining from PRD-001). External observability service configurations that require account setup, API token provisioning, and log drain wiring -- not new application code.
2. **GDPR-compliant account deletion flow** (CS-2 / FSD-012b, ~15% remaining from PRD-008 Phase 3). The request-confirmation-grace-period-hard-delete lifecycle specified in AU-FR-091 that is not covered by PRD-009 (billing/subscriptions) or FSD-011e (onboarding UI).
3. **Command palette (Cmd+K)** (CS-3 / FSD-012c, ~50% remaining from FSD-011a). A searchable modal interface for quick navigation, instrument lookup, trade search, and action execution. This is the largest item in the sweep.
4. **IBKR live market data feed** (CS-4 / FSD-012d, ~2% remaining from PRD-002). Streaming real-time 4H candle data from Interactive Brokers via `ib_async`, replacing the current historical/yfinance data path for live detection.

### 1.2 What This PRD Does NOT Cover

- Team/organization support (PRD-009 scope, Phase 3)
- Onboarding wizard (FSD-011e scope, Phase 3)
- Data export to ZIP (AU-FR-090, will be delivered alongside account deletion but is separately scoped under PRD-008 Phase 3)
- Billing and subscription management (PRD-009)
- Any features from PRD-003 through PRD-007 or PRD-009 through PRD-011

### 1.3 Why a Sweep PRD Exists

The TrendEdge implementation follows a phased rollout across 11 PRDs. Several items were deferred within their parent PRDs -- either because they required external service accounts not available during initial development, because they were explicitly tagged as P2/Phase 3, or because their parent PRD was otherwise feature-complete at >95%. Rather than reopening completed PRDs, this sweep document provides a single tracking point for all residual work.

Each item in this sweep is self-contained. They share no internal dependencies with each other (though they depend on existing infrastructure from earlier PRDs). They can be implemented in any order or in parallel.

### 1.4 Design Principles

1. **Complete what exists.** Every item here has a parent specification (PRD or FSD) with detailed requirements already written. This PRD provides implementation scope and acceptance criteria, not new feature design.
2. **External-first for observability.** Axiom and Uptime Robot are service configurations, not application features. The application already emits structured JSON logs and exposes health endpoints. This work is wiring, not building.
3. **Compliance-driven deletion.** Account deletion is a GDPR requirement with direct legal implications. The grace period, data cascade, and confirmation flow must be exact.
4. **Keyboard-first UX.** The command palette is a power-user feature that reduces mouse dependency and accelerates navigation for active traders.

---

## 2. User Stories

### 2.1 Observability (Axiom + Uptime Robot) -- CS-1 / FSD-012a

| ID | As a... | I want to... | So that... | Priority |
|----|---------|-------------|-----------|----------|
| CS-US-001 | Operator | Have all application logs shipped to Axiom in real time | I can search, filter, and correlate logs across API, worker, and beat services without SSH access | P0 |
| CS-US-002 | Operator | Have Uptime Robot monitoring all health endpoints | I receive alerts within 60 seconds of any service becoming unavailable | P0 |
| CS-US-003 | Operator | See a single Axiom dashboard with request rates, error rates, and p95 latency | I can monitor platform health at a glance | P1 |
| CS-US-004 | Operator | Receive Uptime Robot alerts via email and Telegram | I am notified of downtime through multiple channels regardless of which one is down | P1 |

### 2.2 Account Deletion -- CS-2 / FSD-012b

| ID | As a... | I want to... | So that... | Priority |
|----|---------|-------------|-----------|----------|
| CS-US-010 | Registered user | Delete my account and all associated data permanently | I can exercise my right to be forgotten under GDPR | P0 |
| CS-US-011 | Registered user | Have a 30-day grace period after requesting deletion | I can recover my account if I change my mind | P0 |
| CS-US-012 | Registered user | Receive confirmation emails at each stage of the deletion process | I have a paper trail of the deletion lifecycle | P0 |
| CS-US-013 | Registered user | Re-authenticate before confirming account deletion | My account cannot be deleted by someone with temporary access to my browser | P0 |
| CS-US-014 | Registered user | Have my active subscription cancelled automatically on deletion | I am not charged after my account is deleted | P0 |

### 2.3 Command Palette -- CS-3 / FSD-012c

| ID | As a... | I want to... | So that... | Priority |
|----|---------|-------------|-----------|----------|
| CS-US-020 | Active trader | Open a command palette with Cmd+K | I can navigate the platform without reaching for the mouse | P0 |
| CS-US-021 | Active trader | Search for pages, instruments, and recent trades from the palette | I can jump to any context in under 3 keystrokes | P0 |
| CS-US-022 | Active trader | Execute quick actions (new trade, toggle theme, open settings) from the palette | I can perform common actions without navigating menus | P1 |
| CS-US-023 | Active trader | See fuzzy-matched results with highlighted match characters | I can quickly scan results and confirm my query matched correctly | P1 |
| CS-US-024 | Mobile user | Use keyboard shortcuts on desktop without interfering with text input | Cmd+K is suppressed when I am typing in a form field | P0 |

### 2.4 IBKR Live Market Data Feed -- CS-4 / FSD-012d

| ID | As a... | I want to... | So that... | Priority |
|----|---------|-------------|-----------|----------|
| CS-US-030 | Trader (IBKR) | Have trendline detection use real-time data from my IBKR account | Trendline breaks are detected within seconds of candle close, not on a delayed schedule | P1 |
| CS-US-031 | Trader (IBKR) | Fall back to yfinance data if my IBKR connection is down | Trendline detection continues even if my broker connection drops | P0 |
| CS-US-032 | Operator | Monitor IBKR data feed health alongside other service health | I can see if the live feed is connected, lagging, or failed | P1 |

---

## 3. Functional Requirements

### 3.1 Axiom Log Shipping (FSD-012a)

#### CS-FR-001: Railway Log Drain Configuration

The system SHALL forward all application logs from Railway services (API, Worker, Beat) to Axiom via Railway's native log drain integration.

**Implementation:**
1. Create an Axiom account and dataset named `trendedge-production` (and `trendedge-staging` for staging).
2. Generate an Axiom API token with ingest permissions for the dataset.
3. Configure Railway log drain on each service (`trendedge-api`, `trendedge-worker`, `trendedge-beat`) to forward stdout/stderr to Axiom using the Axiom drain URL: `https://api.axiom.co/v1/datasets/{dataset}/ingest`.
4. Set the `AXIOM_API_TOKEN` environment variable in Railway for each service.
5. Verify that structured JSON logs (as defined in INF-FR-018) arrive in Axiom within 5 seconds of emission.

**Log drain format:** Railway forwards raw stdout lines. Since the application already emits structured JSON (timestamp, level, logger, message, request_id, user_id, duration_ms), Axiom auto-parses these fields for query and filtering.

**Constraints:**
- Axiom free tier: 500MB/day ingest, 30-day retention. Sufficient for MVP scale.
- If free tier limits are exceeded, upgrade to Axiom Personal ($25/mo, 10GB/day).

#### CS-FR-002: Vercel Log Drain Configuration

The system SHALL forward all frontend logs from Vercel to Axiom via the Axiom-Vercel integration.

**Implementation:**
1. Install the Axiom integration from the Vercel Marketplace.
2. Configure the integration to forward logs from the `trendedge-web` Vercel project to the `trendedge-production` Axiom dataset.
3. Verify that Next.js server-side logs and edge function logs appear in Axiom.

#### CS-FR-003: Axiom Dashboard

The system SHALL have a pre-configured Axiom dashboard with the following panels.

| Panel | Query | Visualization |
|---|---|---|
| Request Rate | `count` grouped by `status_code` per 5-minute bucket | Stacked bar chart |
| Error Rate | `count` where `level = "ERROR"` per 5-minute bucket | Line chart with threshold line at 10 errors/5min |
| p95 Latency | `percentile(duration_ms, 95)` per 5-minute bucket | Line chart with threshold line at 200ms |
| Slow Requests | `duration_ms > 1000` sorted by `duration_ms desc` | Table (path, duration_ms, request_id, timestamp) |
| Error Log | `level = "ERROR" OR level = "CRITICAL"` | Table (timestamp, logger, message, request_id) |
| Worker Task Duration | `logger = "trendedge.tasks"`, `percentile(duration_ms, 95)` per task name | Bar chart |

#### CS-FR-004: Axiom Alerting

The system SHALL configure Axiom alerts for critical conditions.

| Alert | Condition | Channel | Severity |
|---|---|---|---|
| High Error Rate | >20 errors in 5 minutes | Email + Telegram | Critical |
| Slow API | p95 latency >2s for 10 consecutive minutes | Email | Warning |
| Worker Failures | >5 task failures in 15 minutes | Email + Telegram | Critical |
| Zero Traffic | 0 requests for 10 minutes during market hours | Email | Warning |

### 3.2 Uptime Robot Monitoring (FSD-012a)

#### CS-FR-010: Health Endpoint Monitors

The system SHALL configure Uptime Robot to monitor all public health endpoints.

| Monitor | URL | Check Interval | Alert Threshold |
|---|---|---|---|
| API Liveness | `https://api.trendedge.io/health` | 60 seconds | 1 failure (immediate alert) |
| API Readiness | `https://api.trendedge.io/health/ready` | 60 seconds | 2 consecutive failures |
| Frontend | `https://app.trendedge.io` | 60 seconds | 2 consecutive failures |
| Staging API | `https://staging-api.trendedge.io/health` | 300 seconds | 3 consecutive failures |

**Monitor configuration:**
- HTTP method: GET
- Expected status code: 200
- Timeout: 30 seconds
- Monitor type: HTTP(s)
- Alert contacts: Email (primary) + Telegram (via Uptime Robot Telegram integration)

#### CS-FR-011: Uptime Robot Status Page

The system SHALL configure a public status page at `https://status.trendedge.io` (or Uptime Robot-hosted equivalent).

**Components displayed:**
- API (maps to API Liveness + Readiness monitors)
- Frontend (maps to Frontend monitor)
- Database (inferred from API Readiness -- readiness check includes database connectivity)
- Real-time Data Feed (future: maps to IBKR feed health, deferred until CS-FR-040+ is implemented)

#### CS-FR-012: Uptime Robot Alert Channels

The system SHALL configure alert notifications through multiple channels.

| Channel | Configuration | Alert Types |
|---|---|---|
| Email | Operator email address | All monitors, all states (down, up, SSL expiry) |
| Telegram | Via Uptime Robot's Telegram bot integration | Production monitors only (down + up notifications) |

---

### 3.3 Account Deletion Flow (FSD-012b)

#### CS-FR-020: Deletion Request Initiation

The system SHALL allow authenticated users to request account deletion from `/settings/account`.

**UI Flow:**
1. User navigates to `/settings/account` and clicks "Delete my account."
2. System displays a confirmation screen with:
   - Warning: "This action is permanent and cannot be undone after the 30-day grace period."
   - Data impact list: "All your data will be permanently deleted, including: trades, journal entries, playbooks, trendlines, signals, broker connections, API keys, and settings."
   - Subscription notice (if applicable): "Your active subscription will be cancelled immediately. No refund will be issued for the current billing period."
   - Broker notice: "All active broker connections will be disconnected."
3. User must type "DELETE" in a confirmation input field. The "Confirm Deletion" button remains disabled until the input matches exactly.
4. User must re-authenticate: enter their password, or confirm via OAuth provider if they registered via OAuth.

**Validation:**
- Input must exactly match the string "DELETE" (case-sensitive).
- Re-authentication must succeed within 5 minutes of initiating the deletion flow. If the session is older than 5 minutes since last authentication, force re-authentication.

#### CS-FR-021: Deletion Processing (Soft Delete)

On successful confirmation, the system SHALL execute the following steps in order.

**Immediate actions (synchronous, within the request):**
1. Set `users.deleted_at = NOW()` (soft delete marker).
2. Set `users.settings -> 'account_status' = 'pending_deletion'`.
3. Revoke all active sessions for the user via Supabase Admin API (`supabase.auth.admin.signOut(user_id, 'global')`).
4. Deactivate all API keys (`api_keys.is_active = false WHERE user_id = :user_id`).

**Asynchronous actions (Celery task, `high` queue):**
1. Cancel active Stripe subscription (if any) via Stripe API. Log the cancellation event.
2. Disconnect all broker connections: revoke OAuth tokens where supported (Tradovate), close WebSocket connections (IBKR). Set all `broker_connections.status = 'disconnected'`.
3. Send confirmation email: "Your TrendEdge account has been scheduled for deletion. All your data will be permanently removed on {deletion_date}. If this was a mistake, you can restore your account by logging in within 30 days."

**Response:** Redirect to `/goodbye` page displaying: "Your account has been scheduled for deletion. You will receive a confirmation email shortly. If you change your mind, you can log in within the next 30 days to restore your account."

#### CS-FR-022: Grace Period (30 Days)

The system SHALL maintain soft-deleted accounts for 30 days before hard deletion.

**During the grace period:**
1. The user can log in. On successful authentication, display a restoration prompt: "Your account is scheduled for deletion on {date}. Would you like to restore your account? [Restore Account] [Continue with Deletion]"
2. If the user clicks "Restore Account":
   a. Clear `users.deleted_at` (set to NULL).
   b. Clear `users.settings -> 'account_status'` (remove key or set to 'active').
   c. Re-activate API keys that were active before deletion (`api_keys.is_active = true WHERE user_id = :user_id AND deactivated_by = 'deletion'`).
   d. Send confirmation email: "Your TrendEdge account has been restored. All your data is intact."
   e. Redirect to `/dashboard`.
3. Broker connections are NOT automatically restored -- the user must re-connect brokers manually (credentials were disconnected, not deleted).
4. If the user had an active subscription, it is NOT automatically restored -- the user must re-subscribe manually.

**Celery Beat scheduled task:** `purge_deleted_accounts` runs daily at 03:00 UTC. It queries for all users where `deleted_at IS NOT NULL AND deleted_at < NOW() - INTERVAL '30 days'`.

#### CS-FR-023: Hard Deletion (After Grace Period)

The `purge_deleted_accounts` task SHALL permanently remove all data for accounts whose grace period has expired.

**Deletion cascade (executed in a single database transaction where possible):**

| Step | Table | Operation | Notes |
|---|---|---|---|
| 1 | `signals` | DELETE WHERE user_id = :id | Trade signals |
| 2 | `order_events` | DELETE via CASCADE from orders | Event history |
| 3 | `orders` | DELETE WHERE user_id = :id | Order records |
| 4 | `positions` | DELETE WHERE user_id = :id | Position records |
| 5 | `risk_check_audits` | DELETE WHERE user_id = :id | Risk audit trail |
| 6 | `user_risk_settings` | DELETE WHERE user_id = :id | Risk configuration |
| 7 | `risk_settings_changelog` | DELETE WHERE user_id = :id | Settings history |
| 8 | `trendlines` | DELETE WHERE user_id = :id | Detected trendlines |
| 9 | `trendline_breaks` | DELETE via CASCADE from trendlines | Break events |
| 10 | `journal_entries` | DELETE WHERE user_id = :id | Journal entries (future) |
| 11 | `playbooks` | DELETE WHERE user_id = :id | Strategy playbooks (future) |
| 12 | `broker_connections` | DELETE WHERE user_id = :id | Encrypted credentials removed |
| 13 | `api_keys` | DELETE WHERE user_id = :id | Webhook keys |
| 14 | `webhook_urls` | DELETE WHERE user_id = :id | Webhook configurations |
| 15 | `audit_logs` | DELETE WHERE user_id = :id | Audit trail (note: legal hold may override) |
| 16 | `users` | DELETE WHERE id = :id | User profile row |
| 17 | `auth.users` | DELETE via Supabase Admin API | Supabase auth record |

**External cleanup (async, best-effort):**
- Delete user avatar from Cloudflare R2 (`avatars/{user_id}.*`).
- Delete any pending data export files from R2.
- Remove user from Sentry user context (if applicable).

**Post-deletion:**
- Send final confirmation email (to the email address captured before deletion): "Your TrendEdge account and all associated data have been permanently deleted. This action cannot be reversed."
- Log the hard deletion event in a separate `deletion_audit_log` table (retains only: anonymized user hash, deletion timestamp, data categories deleted). This log is retained for 2 years for compliance purposes.

#### CS-FR-024: Deletion API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/account/delete` | Authenticated + re-auth | Initiate account deletion (soft delete) |
| POST | `/api/v1/account/restore` | Authenticated (deleted user) | Restore account during grace period |
| GET | `/api/v1/account/deletion-status` | Authenticated | Check deletion status and scheduled date |

**Request schema (POST /api/v1/account/delete):**
```json
{
  "confirmation": "DELETE",
  "password": "user_current_password"
}
```

**Response schema (POST /api/v1/account/delete):**
```json
{
  "status": "scheduled",
  "deletion_date": "2026-03-14T03:00:00Z",
  "message": "Your account has been scheduled for deletion."
}
```

**Error responses:**
| Condition | HTTP Status | Error Code | Message |
|-----------|------------|------------|---------|
| Missing confirmation | 422 | VALIDATION_ERROR | "Confirmation field must be 'DELETE'" |
| Invalid password | 401 | AUTHENTICATION_REQUIRED | "Invalid password. Please try again." |
| OAuth user without password | 422 | VALIDATION_ERROR | "Please re-authenticate via your OAuth provider." |
| Already pending deletion | 409 | CONFLICT | "Account is already scheduled for deletion on {date}." |
| Rate limited | 429 | RATE_LIMITED | "Too many attempts. Please try again later." |

---

### 3.4 Command Palette (FSD-012c)

#### CS-FR-030: Command Palette Component

The system SHALL implement a modal command palette accessible via keyboard shortcut or header button click.

**Trigger:**
- Keyboard: `Cmd+K` (macOS) or `Ctrl+K` (Windows/Linux).
- Click: Magnifying glass icon + "Cmd+K" hint text in the header bar.
- The keyboard shortcut is suppressed when focus is inside an `<input>`, `<textarea>`, or `[contenteditable]` element.

**Appearance:**
- Modal dialog centered on screen, 560px wide, max-height 480px.
- Semi-transparent backdrop (`bg-black/50`).
- Rounded corners (`rounded-lg`), shadow (`shadow-2xl`), background `--popover`.
- Closes on Escape, backdrop click, or result selection.

**Library:** `cmdk` (Command Menu for React) or equivalent headless command palette component. Must support accessible `role="dialog"`, `aria-modal="true"`, `aria-label="Command palette"`, and `role="listbox"` / `role="option"` for results.

#### CS-FR-031: Search Input

The search input SHALL auto-focus on palette open.

- Placeholder: `"Search pages, instruments, trades..."`
- Full width, no border, large text (`text-lg`).
- Debounce strategy: local results (pages, actions) filter instantly (<16ms). API-backed results (recent trades, playbooks) debounce at 200ms.
- Clear button (X icon) appears when input is non-empty.

#### CS-FR-032: Result Categories

Results SHALL display as grouped sections with category headers.

| Category | Source | Max Items | Item Format | Icon |
|---|---|---|---|---|
| Pages | Static list of all 8 navigation pages | 8 | Page icon + Page name | Lucide icons matching sidebar |
| Instruments | Static list of configured instruments (up to 20) | 8 | Symbol + full name + current price + daily change % (colored) | TrendingUp |
| Recent Trades | API: GET `/api/v1/trades?limit=10&sort=-created_at` | 10 | Instrument + direction (Long/Short) + P&L (green/red) + date | ArrowUpRight / ArrowDownRight |
| Playbooks | API: GET `/api/v1/playbooks` | All (up to 20) | Playbook name + trade count | BookOpen |
| Actions | Static list | 5 | Action icon + Action name | See below |

**Static Actions:**
| Action | Icon | Behavior |
|---|---|---|
| New Trade Entry | Plus | Navigate to `/execution`, open trade form |
| New Playbook | BookPlus | Navigate to `/playbooks`, open create form |
| Toggle Theme | Sun/Moon | Switch between light and dark theme |
| Open Settings | Settings | Navigate to `/settings` |
| View Keyboard Shortcuts | Keyboard | Open keyboard shortcuts help dialog |

#### CS-FR-033: Fuzzy Matching

As the user types, results SHALL filter across all categories simultaneously.

- Matching algorithm: case-insensitive substring match for MVP. Matching characters in result labels are rendered in bold (`font-semibold`) with the rest in normal weight.
- Categories with zero matching results are hidden entirely.
- If all categories are empty, display: "No results found for '[query]'" in muted text centered in the results area.

#### CS-FR-034: Keyboard Navigation

The palette SHALL support full keyboard navigation.

| Key | Action |
|---|---|
| Arrow Down | Move highlight to next result (wraps from last to first) |
| Arrow Up | Move highlight to previous result (wraps from first to last) |
| Enter | Select highlighted result (navigate or execute action) |
| Escape | Close the palette |
| Tab | Move highlight to next result (same as Arrow Down) |

- The first result is highlighted by default when the palette opens or when query changes produce new results.
- Category headers are skipped during keyboard navigation (only result items receive focus).

#### CS-FR-035: State Management

The command palette state SHALL be managed via a dedicated Zustand store or local component state.

| State | Display |
|---|---|
| Initial (no query) | All Pages and Actions shown. No API results fetched. |
| Typing (results found) | Filtered results across all categories. API results shown as they resolve. |
| Loading (API) | Skeleton placeholders in API-backed categories while fetching. Static categories display immediately. |
| No results | "No results found for '[query]'" in muted text. |
| API error | Categories with failed API calls are omitted silently. Pages and Actions (static) always display. Toast notification for persistent API errors. |

#### CS-FR-036: Mobile Behavior

On viewports below 768px:
- The header does not display the command palette trigger button (saves horizontal space).
- The `Cmd+K` / `Ctrl+K` keyboard shortcut remains functional if a hardware keyboard is connected.
- The palette modal renders full-width with 16px horizontal margins, max-height 60vh.

---

### 3.5 IBKR Live Market Data Feed (FSD-012d)

#### CS-FR-040: IBKR Streaming Data Connection

The system SHALL support real-time 4H OHLCV candle streaming from Interactive Brokers via the `ib_async` library.

**Connection lifecycle:**
1. On Celery worker startup, if an active IBKR broker connection exists with `is_paper = false` or `is_paper = true` (paper TWS), establish a connection using `ib_async.IB()`.
2. Subscribe to real-time bars for all configured instruments using `ib.reqRealTimeBars()` or `ib.reqHistoricalData()` with `keepUpToDate=True`.
3. On receiving new bar data, aggregate into 4H candles using the same OHLCV schema as the existing `candles` table.
4. On 4H candle close (every 4 hours during market hours), insert the completed candle into PostgreSQL and trigger the trendline detection pipeline for that instrument.

**Connection parameters:**
| Parameter | Value | Notes |
|---|---|---|
| Host | From `broker_connections.credentials` (decrypted) | Default: `127.0.0.1` for local TWS |
| Port | From `broker_connections.credentials` (decrypted) | 4001 (live TWS), 4002 (paper TWS), 7496 (live Gateway), 7497 (paper Gateway) |
| Client ID | Auto-assigned per worker (100 + worker_index) | Avoids conflicts with other IBKR API clients |
| Timeout | 30 seconds for connection, 10 seconds for requests | |
| Reconnect | Automatic with exponential backoff (5s, 10s, 20s, 60s max) | Max 10 retries before circuit breaker trips |

#### CS-FR-041: Data Source Priority

The system SHALL use a tiered data source strategy for 4H candle ingestion.

| Priority | Source | Condition | Latency |
|---|---|---|---|
| 1 | IBKR live stream | Active IBKR connection with `ib_async` | <5 seconds after candle close |
| 2 | IBKR historical API | IBKR connected but stream interrupted | <30 seconds (poll-based fallback) |
| 3 | Tradovate WebSocket | Active Tradovate connection, no IBKR | <15 seconds |
| 4 | yfinance | No broker connections, or all broker feeds failed | <60 seconds (delayed data, daily timeframe only) |

**Fallback behavior:**
- If the primary IBKR stream disconnects, the system automatically falls back to Priority 2 (IBKR historical poll) within one candle period.
- If all IBKR methods fail for 3 consecutive candle periods, the system falls back to Priority 3 or 4 and logs a warning.
- When the primary source recovers, the system switches back automatically on the next candle period.
- All fallback transitions are logged at INFO level with the source change reason.

#### CS-FR-042: IBKR Feed Health Monitoring

The system SHALL expose IBKR data feed health in the existing health check infrastructure.

**Health check addition to `/health/detailed`:**
```json
{
  "checks": {
    "ibkr_feed": {
      "status": "ok",
      "connected_since": "2026-02-12T14:00:00Z",
      "instruments_subscribed": 6,
      "last_bar_received": "2026-02-12T18:00:00Z",
      "latency_ms": 45,
      "source_priority": 1
    }
  }
}
```

**Status values:**
| Status | Meaning |
|---|---|
| `ok` | Connected and receiving data within expected intervals |
| `degraded` | Connected but data delayed >60 seconds, or on fallback source |
| `error` | Disconnected, all retries exhausted, circuit breaker open |
| `not_configured` | No IBKR broker connection exists |

#### CS-FR-043: Circuit Breaker for IBKR Feed

The system SHALL apply the existing circuit breaker pattern (3 consecutive failures, 15-minute cooldown) to the IBKR data feed connection.

**Behavior:**
1. After 3 consecutive connection failures or 3 consecutive data request timeouts, the circuit breaker trips.
2. While tripped, the system uses the next available data source in the priority chain (CS-FR-041).
3. After 15 minutes, the circuit breaker enters half-open state and attempts a single IBKR reconnection.
4. On success: circuit closes, IBKR becomes primary source again.
5. On failure: circuit re-opens for another 15 minutes.
6. Circuit breaker state is stored in Redis (`circuit_breaker:ibkr_feed:{user_id}`).

#### CS-FR-044: Contract Symbol Mapping for Live Data

The system SHALL map continuous contract symbols to IBKR-specific contract objects when subscribing to live data.

**Mapping (uses existing `contract_specifications` and `contract_calendar` tables from PRD-002):**
| Continuous Symbol | IBKR Contract | Exchange |
|---|---|---|
| ES | ES + current front-month | CME |
| NQ | NQ + current front-month | CME |
| YM | YM + current front-month | CBOT |
| CL | CL + current front-month | NYMEX |
| GC | GC + current front-month | COMEX |
| PL | PL + current front-month | NYMEX |

The front-month contract is determined by the existing roll logic defined in TD-FR-100 through TD-FR-103. The live feed subscription must update its contract symbol on roll dates.

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Target | Measurement | Sub-FSD |
|---|---|---|---|---|
| CS-NFR-001 | Axiom log ingestion latency | <5 seconds from emission to Axiom availability | Manual verification: emit log, query in Axiom | FSD-012a |
| CS-NFR-002 | Uptime Robot alert delivery | <90 seconds from failure to alert receipt | Simulated failure test | FSD-012a |
| CS-NFR-003 | Account deletion (soft delete) response time | <2 seconds | Includes session revocation and task dispatch | FSD-012b |
| CS-NFR-004 | Account deletion (hard delete) execution time | <60 seconds per account | Background task, no user-facing latency | FSD-012b |
| CS-NFR-005 | Command palette open-to-render | <100ms | From keypress to visible modal with static results | FSD-012c |
| CS-NFR-006 | Command palette local filtering | <16ms per keystroke | No frame drops during typing | FSD-012c |
| CS-NFR-007 | Command palette API results | <300ms total (200ms debounce + 100ms render) | From keystroke to rendered API results | FSD-012c |
| CS-NFR-008 | IBKR live data candle delivery | <5 seconds after candle close | From IBKR server emission to PostgreSQL insert | FSD-012d |

### 4.2 Reliability

| ID | Requirement | Target | Notes | Sub-FSD |
|---|---|---|---|---|
| CS-NFR-010 | Uptime Robot monitoring availability | 99.9% check execution | Uptime Robot's own SLA | FSD-012a |
| CS-NFR-011 | Account deletion data completeness | 100% of user data removed | Verified by post-deletion audit query | FSD-012b |
| CS-NFR-012 | IBKR feed reconnection | Auto-reconnect within 60 seconds of transient failure | Exponential backoff, max 10 retries | FSD-012d |
| CS-NFR-013 | Command palette availability | Functions offline for static categories | Pages and Actions work without API connectivity | FSD-012c |

### 4.3 Security

| ID | Requirement | Target | Notes | Sub-FSD |
|---|---|---|---|---|
| CS-NFR-020 | Axiom API token | Stored in Railway encrypted environment variables | Never logged, never in source control | FSD-012a |
| CS-NFR-021 | Account deletion re-authentication | Required within 5 minutes of deletion request | Prevents stale-session abuse | FSD-012b |
| CS-NFR-022 | Deletion audit log | Immutable, 2-year retention | Append-only table, no UPDATE/DELETE policies | FSD-012b |
| CS-NFR-023 | Post-deletion data residue | Zero user-identifiable data remains after hard delete | Verified by compliance scan query | FSD-012b |

### 4.4 Compliance

| ID | Requirement | Standard | Notes | Sub-FSD |
|---|---|---|---|---|
| CS-NFR-030 | Right to erasure | GDPR Article 17 | Account deletion flow satisfies the right to be forgotten | FSD-012b |
| CS-NFR-031 | Data portability | GDPR Article 20 | Data export (AU-FR-090, separate scope) complements deletion | FSD-012b |
| CS-NFR-032 | Deletion confirmation | GDPR Article 12 | Email confirmations at each lifecycle stage provide transparency | FSD-012b |

---

## 5. Dependencies

### 5.1 Infrastructure Dependencies

| Dependency | Required For | Sub-FSD | Impact if Missing |
|-----------|-------------|---------|------------------|
| Axiom account + API token | CS-FR-001 through CS-FR-004 | FSD-012a | No centralized log aggregation; logs only in Railway console (limited retention) |
| Uptime Robot account | CS-FR-010 through CS-FR-012 | FSD-012a | No external uptime monitoring; failures may go undetected |
| Railway log drain feature | CS-FR-001 | FSD-012a | Cannot forward logs to Axiom; must use alternative (direct API push from app) |
| Stripe API (if subscription exists) | CS-FR-021 | FSD-012b | Cannot auto-cancel subscriptions on deletion; manual cancellation required |
| Supabase Admin API | CS-FR-021, CS-FR-023 | FSD-012b | Cannot revoke sessions or delete auth.users records |
| `cmdk` or equivalent React library | CS-FR-030 | FSD-012c | Must build command palette from scratch (increased scope) |
| `ib_async` Python library | CS-FR-040 through CS-FR-044 | FSD-012d | Cannot connect to IBKR TWS/Gateway for live data |
| Active IBKR TWS or Gateway instance | CS-FR-040 | FSD-012d | No live data source; system falls back to yfinance |

### 5.2 PRD Dependencies

| PRD | Items Dependent On | Sub-FSD | Required Features |
|-----|-------------------|---------|------------------|
| PRD-001 (Infrastructure) | CS-FR-001 through CS-FR-012 | FSD-012a | Structured JSON logging (INF-FR-018), health endpoints (INF-FR-015), Railway deployment |
| PRD-002 (Trendline Detection) | CS-FR-040 through CS-FR-044 | FSD-012d | Candle data schema, trendline detection pipeline, contract specifications (TD-FR-100-103) |
| PRD-008 (Auth & User Management) | CS-FR-020 through CS-FR-024 | FSD-012b | User model, RLS policies, session management (AU-FR-010-013), broker connections (AU-FR-040-044) |
| FSD-011a (App Shell) | CS-FR-030 through CS-FR-036 | FSD-012c | Header bar layout, sidebar navigation, theme system, keyboard shortcut framework |

---

## 6. Testing Requirements

### 6.1 Observability Testing (FSD-012a)

#### CS-TEST-001: Log Shipping Verification

| Test Case | Method | Expected Outcome |
|-----------|--------|-----------------|
| API log appears in Axiom | Trigger a known API request, search Axiom for the request_id | Log entry found within 10 seconds with all structured fields |
| Worker log appears in Axiom | Trigger a Celery task, search Axiom for the task_id | Log entry found within 10 seconds |
| Error log appears in Axiom | Trigger a deliberate error, search Axiom for level=ERROR | Error log found with stack context (no raw stack trace) |
| Axiom dashboard loads | Open Axiom dashboard URL | All 6 panels render with data from the last hour |

#### CS-TEST-002: Uptime Monitoring Verification

| Test Case | Method | Expected Outcome |
|-----------|--------|-----------------|
| Downtime detection | Stop API service temporarily | Uptime Robot alert received within 90 seconds |
| Recovery detection | Restart API service | Uptime Robot "Up" notification received within 120 seconds |
| Status page reflects state | Check status page during downtime | API component shows "Down" status |

### 6.2 Account Deletion Testing (FSD-012b)

#### CS-TEST-010: Deletion Flow Testing

| Test Case | Input | Expected Outcome |
|-----------|-------|-----------------|
| Valid deletion request | confirmation="DELETE", valid password | Account soft-deleted, sessions revoked, email sent |
| Wrong confirmation string | confirmation="delete" (lowercase) | 422 error: confirmation must be "DELETE" |
| Wrong password | confirmation="DELETE", invalid password | 401 error: invalid password |
| Already pending deletion | Second deletion request | 409 error: already scheduled |
| Deletion with active subscription | User has Stripe subscription | Subscription cancelled, deletion proceeds |
| Deletion with broker connections | User has 2 active brokers | Both disconnected, credentials retained (soft delete) |

#### CS-TEST-011: Grace Period Testing

| Test Case | Setup | Expected Outcome |
|-----------|-------|-----------------|
| Login during grace period | Soft-deleted user logs in | Restoration prompt displayed |
| Account restoration | User clicks "Restore Account" | deleted_at cleared, API keys re-activated, confirmation email sent |
| Grace period expiry | Advance clock 31 days | purge_deleted_accounts task hard-deletes all user data |
| Post-hard-delete login | Attempt login after hard delete | "Invalid email or password" (account no longer exists) |

#### CS-TEST-012: Data Completeness Verification

| Test Case | Method | Expected Outcome |
|-----------|--------|-----------------|
| All tables cleaned | After hard delete, query all user-owned tables | Zero rows returned for the deleted user_id across all tables |
| Auth record removed | Query auth.users for deleted user | Zero rows returned |
| R2 files removed | Check R2 for avatar and export files | Files not found (404) |
| Deletion audit log exists | Query deletion_audit_log | Entry exists with anonymized hash and timestamp |

### 6.3 Command Palette Testing (FSD-012c)

#### CS-TEST-020: Functional Testing

| Test Case | Input | Expected Outcome |
|-----------|-------|-----------------|
| Open via Cmd+K | Press Cmd+K on macOS | Palette modal opens, search input focused |
| Open via Ctrl+K | Press Ctrl+K on Windows/Linux | Palette modal opens, search input focused |
| Open via header button | Click magnifying glass icon | Palette modal opens, search input focused |
| Suppressed in input | Focus a text input, press Cmd+K | Palette does NOT open |
| Close via Escape | Press Escape | Palette closes |
| Close via backdrop click | Click outside the palette modal | Palette closes |
| Navigate to page | Type "dash", press Enter | Palette closes, navigates to /dashboard |
| Filter results | Type "journal" | Only matching results displayed across categories |
| No results | Type "xyznonexistent" | "No results found for 'xyznonexistent'" displayed |
| Arrow key navigation | Open palette, press Down 3 times, press Enter | Third result selected and executed |
| Execute action | Select "Toggle Theme" | Theme switches, palette closes |

#### CS-TEST-021: Accessibility Testing

| Test Case | Method | Expected Outcome |
|-----------|--------|-----------------|
| Screen reader announcement | Open palette with VoiceOver | "Command palette" dialog announced |
| Listbox semantics | Inspect DOM | Results use role="listbox", items use role="option" |
| Focus trap | Tab through palette | Focus cycles within palette, does not escape to background |
| aria-activedescendant | Navigate with arrow keys | Active result announced by screen reader |

### 6.4 IBKR Live Feed Testing (FSD-012d)

#### CS-TEST-030: Connection Testing

| Test Case | Setup | Expected Outcome |
|-----------|-------|-----------------|
| Successful connection | IBKR Paper TWS running on port 4002 | Connection established, instruments subscribed |
| Connection failure | TWS not running | Fallback to yfinance, warning logged |
| Connection timeout | TWS running but unresponsive | Timeout after 30 seconds, retry with backoff |
| Circuit breaker trip | 3 consecutive failures | Circuit opens, fallback to next source, 15-min cooldown |
| Circuit breaker recovery | TWS restarted during half-open | Circuit closes, IBKR primary again |
| Contract roll | Front-month contract expires | Subscription updates to new front-month |

#### CS-TEST-031: Data Integrity Testing

| Test Case | Method | Expected Outcome |
|-----------|--------|-----------------|
| Candle completeness | Compare IBKR candles with yfinance for same period | OHLCV values match within 0.1% tolerance |
| No duplicate candles | Subscribe and wait for multiple candle periods | Each (instrument, timestamp) pair appears exactly once |
| Gap detection | Disconnect IBKR for 8 hours, reconnect | Gap-fill process fills missing candles |
| Trendline trigger | Receive new 4H candle via live feed | Trendline detection pipeline executes within 10 seconds |

---

## 7. Acceptance Criteria

### 7.1 Observability Acceptance Criteria (FSD-012a)

| ID | Criterion | Verification Method |
|----|----------|-------------------|
| CS-AC-001 | All API, Worker, and Beat logs appear in Axiom within 10 seconds | Manual: trigger requests across all services, verify in Axiom query |
| CS-AC-002 | Axiom dashboard renders all 6 panels with live data | Manual: open dashboard, verify non-empty panels |
| CS-AC-003 | Axiom alerts fire for simulated high error rate | Manual: emit >20 ERROR logs in 5 minutes, verify alert delivery |
| CS-AC-004 | Uptime Robot detects API downtime within 90 seconds | Manual: stop API, measure time to alert receipt |
| CS-AC-005 | Uptime Robot status page shows correct component states | Manual: verify during normal operation and simulated downtime |
| CS-AC-006 | Vercel logs appear in Axiom | Manual: trigger server-side log in Next.js, verify in Axiom |

### 7.2 Account Deletion Acceptance Criteria (FSD-012b)

| ID | Criterion | Verification Method |
|----|----------|-------------------|
| CS-AC-010 | User can request deletion with "DELETE" confirmation + re-auth | Automated test: POST /api/v1/account/delete with valid payload |
| CS-AC-011 | Soft delete revokes all sessions and deactivates API keys | Automated test: verify session tokens return 401, API keys return 401 |
| CS-AC-012 | Confirmation email sent with correct deletion date (30 days out) | Automated test: verify email queued with correct date |
| CS-AC-013 | User can log in during grace period and see restoration prompt | E2E test: soft-delete, log in, verify prompt renders |
| CS-AC-014 | Account restoration clears deleted_at and re-activates API keys | Automated test: restore, verify DB state, verify API keys work |
| CS-AC-015 | Hard delete removes ALL user data from ALL tables | Automated test: run purge task, query all 17 tables for user_id, verify 0 rows each |
| CS-AC-016 | Hard delete removes auth.users record | Automated test: query Supabase auth.users, verify 0 rows |
| CS-AC-017 | Stripe subscription cancelled on deletion (if active) | Automated test: mock Stripe API, verify cancellation call |
| CS-AC-018 | Deletion audit log retains anonymized record for 2 years | Automated test: verify deletion_audit_log entry exists after hard delete |

### 7.3 Command Palette Acceptance Criteria (FSD-012c)

| ID | Criterion | Verification Method |
|----|----------|-------------------|
| CS-AC-020 | Cmd+K opens the command palette on macOS | E2E test: keypress simulation, verify modal visible |
| CS-AC-021 | Ctrl+K opens the command palette on Windows/Linux | E2E test: keypress simulation |
| CS-AC-022 | Cmd+K is suppressed when focus is in a text input | E2E test: focus input, press Cmd+K, verify palette does NOT open |
| CS-AC-023 | Static results (Pages, Actions) render in <100ms | Performance test: measure open-to-render time |
| CS-AC-024 | Typing filters results with highlighted match characters | E2E test: type "dash", verify "Dashboard" appears with "dash" bolded |
| CS-AC-025 | Arrow keys navigate results, Enter selects | E2E test: open palette, press Down 2x, press Enter, verify navigation |
| CS-AC-026 | Escape closes the palette | E2E test: open, press Escape, verify modal hidden |
| CS-AC-027 | "No results" message displays for unmatched queries | E2E test: type gibberish, verify empty state message |
| CS-AC-028 | Palette has correct ARIA roles and labels | Accessibility test: axe-core scan of open palette, zero critical violations |
| CS-AC-029 | Mobile viewport: palette renders full-width with margins | E2E test: 375px viewport, open palette, verify dimensions |

### 7.4 IBKR Live Feed Acceptance Criteria (FSD-012d)

| ID | Criterion | Verification Method |
|----|----------|-------------------|
| CS-AC-030 | System connects to IBKR TWS/Gateway on worker startup | Integration test: start worker with TWS running, verify connection log |
| CS-AC-031 | Live 4H candles inserted within 5 seconds of candle close | Integration test: wait for candle close, measure insert latency |
| CS-AC-032 | Trendline detection triggers on live candle insert | Integration test: insert candle, verify detection task dispatched |
| CS-AC-033 | Fallback to yfinance on IBKR connection failure | Integration test: stop TWS, verify yfinance data continues |
| CS-AC-034 | Circuit breaker trips after 3 consecutive failures | Integration test: simulate 3 failures, verify circuit state in Redis |
| CS-AC-035 | Health endpoint reports IBKR feed status | Integration test: GET /health/detailed, verify ibkr_feed section present |
| CS-AC-036 | Contract symbol updates on roll date | Integration test: simulate roll, verify subscription uses new front-month |

---

## 8. Phase Mapping

This PRD is a single-phase sweep organized into four sub-phases. Each sub-phase maps to its own sub-FSD, following the same pattern as other PRDs (e.g., PRD-003 maps to FSD-003a through FSD-003d). Sub-phases have no internal dependencies and can be executed in parallel or in any order.

### Sub-FSD Mapping

| Sub-Phase | Sub-FSD | Title | Functional Requirements | User Stories | Acceptance Criteria |
|-----------|---------|-------|------------------------|-------------|-------------------|
| CS-1 | FSD-012a | Observability Setup | CS-FR-001 through CS-FR-012 | CS-US-001 through CS-US-004 | CS-AC-001 through CS-AC-006 |
| CS-2 | FSD-012b | Account Deletion | CS-FR-020 through CS-FR-024 | CS-US-010 through CS-US-014 | CS-AC-010 through CS-AC-018 |
| CS-3 | FSD-012c | Command Palette | CS-FR-030 through CS-FR-036 | CS-US-020 through CS-US-024 | CS-AC-020 through CS-AC-029 |
| CS-4 | FSD-012d | IBKR Live Data Feed | CS-FR-040 through CS-FR-044 | CS-US-030 through CS-US-032 | CS-AC-030 through CS-AC-036 |

Each sub-FSD SHALL contain the implementation details, code examples, component specifications, and step-by-step instructions for its sub-phase. The sub-FSDs expand on the functional requirements defined here with exact file paths, function signatures, configuration snippets, and test implementations.

---

### CS-1 / FSD-012a: Observability Setup (Axiom + Uptime Robot)

**Estimated effort:** 1-2 days (external configuration, minimal code changes)

**Goal:** Complete the observability stack defined in PRD-001 by connecting to external monitoring services.

| Requirement | ID | Priority | Notes |
|------------|-----|----------|-------|
| Railway log drain to Axiom | CS-FR-001 | P0 | External service configuration |
| Vercel log drain to Axiom | CS-FR-002 | P0 | Vercel Marketplace integration |
| Axiom dashboard | CS-FR-003 | P1 | Pre-built dashboard panels |
| Axiom alerting | CS-FR-004 | P1 | Alert rules for critical conditions |
| Uptime Robot health monitors | CS-FR-010 | P0 | 4 monitors across prod + staging |
| Uptime Robot status page | CS-FR-011 | P1 | Public status page |
| Uptime Robot alert channels | CS-FR-012 | P0 | Email + Telegram alerts |

**Definition of Done (CS-1):**
- All Railway service logs appear in Axiom within 10 seconds.
- Vercel logs appear in Axiom.
- Axiom dashboard renders with live data.
- Uptime Robot monitors are active for all 4 endpoints.
- Downtime alert delivered within 90 seconds of simulated failure.

### CS-2 / FSD-012b: Account Deletion

**Estimated effort:** 3-5 days (backend endpoints, Celery tasks, frontend UI, email templates)

**Goal:** Implement the GDPR-compliant account deletion lifecycle from PRD-008 AU-FR-091.

| Requirement | ID | Priority | Notes |
|------------|-----|----------|-------|
| Deletion request initiation | CS-FR-020 | P0 | UI + API endpoint |
| Soft delete processing | CS-FR-021 | P0 | Session revocation, subscription cancellation, email |
| 30-day grace period | CS-FR-022 | P0 | Login restoration flow |
| Hard deletion task | CS-FR-023 | P0 | Celery Beat daily task, full data cascade |
| API endpoints | CS-FR-024 | P0 | DELETE, restore, status check |

**Definition of Done (CS-2):**
- User can request deletion with confirmation + re-auth.
- All sessions revoked and API keys deactivated on soft delete.
- User can restore account within 30 days.
- Hard delete removes all data from all tables after grace period.
- Confirmation emails sent at each lifecycle stage.
- Deletion audit log retained.

### CS-3 / FSD-012c: Command Palette

**Estimated effort:** 3-4 days (React component, keyboard handling, API integration, accessibility)

**Goal:** Implement the command palette specified in FSD-011a Section 3.5.

| Requirement | ID | Priority | Notes |
|------------|-----|----------|-------|
| Palette component | CS-FR-030 | P0 | Modal, trigger, library selection |
| Search input | CS-FR-031 | P0 | Auto-focus, debounce, clear |
| Result categories | CS-FR-032 | P0 | Pages, Instruments, Trades, Playbooks, Actions |
| Fuzzy matching | CS-FR-033 | P0 | Substring match with highlight |
| Keyboard navigation | CS-FR-034 | P0 | Arrow keys, Enter, Escape |
| State management | CS-FR-035 | P0 | Loading, empty, error states |
| Mobile behavior | CS-FR-036 | P1 | Full-width modal, hidden trigger |

**Definition of Done (CS-3):**
- Cmd+K / Ctrl+K opens the palette on all platforms.
- Static results (Pages, Actions) render within 100ms.
- API-backed results (Trades, Playbooks) render within 300ms.
- Full keyboard navigation works (arrow keys, Enter, Escape).
- Suppressed in text inputs.
- Passes axe-core accessibility scan with zero critical violations.
- Works correctly on mobile viewports.

### CS-4 / FSD-012d: IBKR Live Market Data Feed

**Estimated effort:** 3-5 days (ib_async integration, data pipeline, circuit breaker, health check)

**Goal:** Connect the trendline detection pipeline to real-time IBKR data.

| Requirement | ID | Priority | Notes |
|------------|-----|----------|-------|
| IBKR streaming connection | CS-FR-040 | P1 | ib_async, worker lifecycle |
| Data source priority chain | CS-FR-041 | P0 | IBKR > Tradovate > yfinance fallback |
| Feed health monitoring | CS-FR-042 | P1 | Health check integration |
| Circuit breaker | CS-FR-043 | P0 | 3 failures, 15-min cooldown |
| Contract symbol mapping | CS-FR-044 | P0 | Continuous-to-specific via existing roll logic |

**Definition of Done (CS-4):**
- System connects to IBKR TWS/Gateway and subscribes to configured instruments.
- Live 4H candles are inserted within 5 seconds of candle close.
- Trendline detection pipeline triggers automatically on live candle insert.
- Fallback chain works (IBKR down -> yfinance continues).
- Circuit breaker trips after 3 failures and recovers after 15-minute cooldown.
- Health endpoint reports IBKR feed status.

---

## 9. Cross-References to Other PRDs

### 9.1 Parent PRD/FSD References

| PRD/FSD | Relationship | Sub-FSD | Specific Items |
|---------|-------------|---------|----------------|
| PRD-001 (Platform Infrastructure) | **Completes** remaining ~5% | FSD-012a | INF-FR-018 (logging, Axiom destination), INF-US-009 (Uptime Robot), INF-US-015 (monitoring dashboard) |
| PRD-002 (Trendline Detection) | **Completes** remaining ~2% | FSD-012d | TD-FR-004 (IBKR intraday data), candle schema, detection pipeline trigger |
| PRD-008 (Auth & User Management) | **Completes** remaining ~15% standalone items | FSD-012b | AU-FR-091 (account deletion), AU-FR-090 (data export, prerequisite only) |
| FSD-011a (App Shell) | **Completes** remaining ~50% | FSD-012c | FE-FR-005 (command palette), Sections 3.5.1-3.5.8, keyboard shortcuts |

### 9.2 Downstream and Intersecting PRDs

| PRD/FSD | Relationship | Sub-FSD | Specific Items |
|---------|-------------|---------|----------------|
| PRD-003 (Trade Execution) | **Unblocked by** CS-4 | FSD-012d | IBKR live data feed provides real-time candles for signal generation |
| PRD-009 (Billing) | **Intersects** CS-2 | FSD-012b | Stripe subscription cancellation on account deletion |
| PRD-010 (Notifications) | **Intersects** CS-1 | FSD-012a | Telegram alerts configured via Uptime Robot; Axiom alerts via email |

### 9.3 Sub-FSD File Mapping

| Sub-FSD | File | Contents |
|---------|------|----------|
| FSD-012a | `_docs/fsd/FSD-012a-observability-setup.md` | Axiom account setup, Railway/Vercel log drain configuration, dashboard panel definitions, Uptime Robot monitor setup, alert channel wiring |
| FSD-012b | `_docs/fsd/FSD-012b-account-deletion.md` | Deletion API endpoints, Celery task implementation, soft/hard delete state machine, grace period logic, email templates, frontend UI for `/settings/account` deletion flow and `/goodbye` page |
| FSD-012c | `_docs/fsd/FSD-012c-command-palette.md` | React component specification, `cmdk` integration, result category rendering, keyboard navigation, fuzzy matching, API integration hooks, accessibility implementation, mobile adaptation |
| FSD-012d | `_docs/fsd/FSD-012d-ibkr-live-feed.md` | `ib_async` connection manager, real-time bar subscription, 4H candle aggregation, data source fallback chain, circuit breaker integration, health check extension, contract roll handling |

---

*This document is PRD-012 of the TrendEdge platform. It is a sweep of residual items from PRD-001, PRD-002, PRD-008, and FSD-011a. Each sub-phase (CS-1 through CS-4) maps to a corresponding sub-FSD (FSD-012a through FSD-012d). All items are self-contained and can be implemented independently.*
