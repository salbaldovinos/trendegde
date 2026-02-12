# PRD-009: Billing & Subscription Management

**TrendEdge — AI-Powered Futures Trading Platform**

Version 1.0 · February 2026 · CONFIDENTIAL

| Field | Value |
|---|---|
| PRD Number | PRD-009 of 11 |
| Feature Area | Billing & Subscription Management |
| Owner | TrendEdge Product Team |
| Status | Draft |
| Phase | Phase 3 (Multi-Tenant SaaS Launch) |
| Dependencies | PRD-001 (Infrastructure), PRD-008 (Auth & User Management) |
| Payment Processor | Stripe |

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Dependencies](#5-dependencies)
6. [Testing Requirements](#6-testing-requirements)
7. [Security](#7-security)
8. [Phase Mapping](#8-phase-mapping)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. Overview & Purpose

### Problem Statement

TrendEdge operates a four-tier subscription model (Free, Trader, Pro, Team) that must enforce feature access, process payments reliably, and minimize revenue leakage — all while maintaining a frictionless user experience for futures traders who expect platform stability during market hours.

### Purpose

This PRD defines the complete billing and subscription management system for TrendEdge, covering Stripe integration, subscription lifecycle management, feature gating, webhook processing, usage metering, and revenue analytics. The billing system is a Phase 3 deliverable — Phases 1 and 2 operate as a single-user system with no billing requirements.

### Scope

**In scope:**
- Stripe product/price configuration and checkout
- Subscription lifecycle (create, upgrade, downgrade, cancel, reactivate)
- Feature gating engine tied to subscription tiers
- Webhook handling for payment events
- Invoice and receipt management
- Usage metering for AI features (Claude API costs)
- Trial period support (14-day Pro trial)
- Coupon and promotion code support
- Admin revenue analytics dashboard
- Refund processing
- Dunning management for failed payments

**Out of scope:**
- Custom enterprise pricing (future consideration)
- Marketplace/strategy sales revenue sharing (Phase 4)
- Cryptocurrency payment methods
- Tax calculation beyond Stripe Tax defaults
- Multi-currency pricing (USD only at launch)

### Tier Structure Reference

| Capability | Free | Trader ($49/mo) | Pro ($99/mo) | Team ($199/mo) |
|---|---|---|---|---|
| Trendline Detection | 3 instruments, delayed | 10 instruments, real-time | Unlimited, real-time | Unlimited + custom |
| Trade Execution | Paper only | 1 broker, 1 account | 3 brokers, 5 accounts | Unlimited accounts |
| Journaling | 10 trades/month | Unlimited | Unlimited + AI review | Unlimited + sharing |
| Playbooks | 1 default | 5 custom | Unlimited | Unlimited + templates |
| Analytics | 5 basic metrics | 25+ full dashboard | Advanced + Monte Carlo | Everything + team |
| Notifications | Email only | Telegram + Email | All channels | All + custom hooks |
| Support | Community | Email (48h) | Priority (24h) | Dedicated (4h) |
| Monthly Price | $0 | $49 | $99 | $199 |
| Annual Price | -- | $399/yr (32% off) | $799/yr (33% off) | $1,899/yr (21% off) |

### Unit Economics Targets

| Metric | Target |
|---|---|
| ARPU | $79/month |
| CAC | <$50 |
| Monthly Churn | <5% |
| Average Customer Lifetime | 14-18 months |
| LTV | $1,100-1,400 |
| LTV:CAC | >20:1 |

---

## 2. User Stories

### 2.1 Subscription Management

| ID | Role | Story | Priority |
|---|---|---|---|
| US-001 | New User | As a new user, I want to start using TrendEdge immediately on the Free tier without providing payment information, so that I can evaluate the platform risk-free. | P0 |
| US-002 | Free User | As a Free tier user, I want to upgrade to a paid plan with a clear comparison of what I gain, so that I can make an informed purchasing decision. | P0 |
| US-003 | Subscriber | As a subscriber, I want to manage my billing (update card, change plan, view invoices) through a self-service portal, so that I do not need to contact support. | P0 |
| US-004 | Subscriber | As a subscriber, I want to switch between monthly and annual billing, so that I can save money with an annual commitment. | P0 |
| US-005 | New User | As a prospective customer, I want to try Pro features for 14 days free, so that I can experience the full platform before committing. | P1 |
| US-006 | Subscriber | As a subscriber, I want to apply a promotion code during checkout, so that I can take advantage of discounts. | P1 |
| US-007 | Subscriber | As a subscriber with a failed payment, I want clear communication about what happened and how to fix it, so that I do not lose access unexpectedly. | P0 |

### 2.2 Upgrades & Downgrades

| ID | Role | Story | Priority |
|---|---|---|---|
| US-008 | Free User | As a Free user who hit the 10-trade journal limit, I want to upgrade inline without losing my current workflow, so that I can continue journaling immediately. | P0 |
| US-009 | Trader User | As a Trader subscriber, I want to upgrade to Pro mid-cycle and only pay the prorated difference, so that I am not double-charged. | P0 |
| US-010 | Pro User | As a Pro subscriber, I want to downgrade to Trader at my next billing cycle, so that I can reduce costs while keeping access until the period ends. | P0 |
| US-011 | Team User | As a Team subscriber who wants to downgrade, I want to see exactly which features and data I will lose, so that I can prepare before the change takes effect. | P0 |
| US-012 | Subscriber | As a subscriber who cancelled, I want to reactivate my subscription and retain my historical data, so that I can pick up where I left off. | P1 |

### 2.3 Admin & Operations

| ID | Role | Story | Priority |
|---|---|---|---|
| US-013 | Admin | As an admin, I want a revenue analytics dashboard showing MRR, churn, LTV, and subscription distribution, so that I can monitor business health. | P1 |
| US-014 | Admin | As an admin, I want to issue refunds and apply credits through an admin panel, so that I can handle customer service requests efficiently. | P1 |
| US-015 | Admin | As an admin, I want to create and manage coupon codes with configurable rules (percentage off, fixed amount, duration, usage limits), so that I can run promotions. | P1 |
| US-016 | Admin | As an admin, I want to monitor AI feature usage costs per user, so that I can ensure Claude API costs do not exceed revenue margins. | P2 |

---

## 3. Functional Requirements

### 3.1 Stripe Integration

#### BL-FR-001: Stripe Product and Price Configuration

The system SHALL configure Stripe products and prices for all four tiers across both billing intervals.

**Products (4):**

| Product Name | Stripe Product ID Pattern | Description |
|---|---|---|
| TrendEdge Free | `prod_trendedge_free` | Free tier — no Stripe price required |
| TrendEdge Trader | `prod_trendedge_trader` | Trader tier subscription |
| TrendEdge Pro | `prod_trendedge_pro` | Pro tier subscription |
| TrendEdge Team | `prod_trendedge_team` | Team tier subscription |

**Prices (6 recurring):**

| Price | Amount | Interval | Stripe Price ID Pattern |
|---|---|---|---|
| Trader Monthly | $49.00 | month | `price_trader_monthly` |
| Trader Annual | $399.00 | year | `price_trader_annual` |
| Pro Monthly | $99.00 | month | `price_pro_monthly` |
| Pro Annual | $799.00 | year | `price_pro_annual` |
| Team Monthly | $199.00 | month | `price_team_monthly` |
| Team Annual | $1,899.00 | year | `price_team_annual` |

**Implementation:**
- Products and prices SHALL be created via Stripe Dashboard or seed script (not dynamically at runtime).
- Price IDs SHALL be stored in environment configuration, not hardcoded.
- All prices use `currency: usd` and `recurring` mode.
- Metadata on each product SHALL include `tier_level` (0=Free, 1=Trader, 2=Pro, 3=Team) for programmatic comparison.

#### BL-FR-002: Checkout Session Creation

The system SHALL create Stripe Checkout Sessions for new subscriptions.

**Checkout flow:**
1. User selects a plan and billing interval on the pricing page.
2. Frontend calls `POST /api/billing/checkout` with `{ price_id, billing_interval }`.
3. Backend creates a Stripe Checkout Session with:
   - `mode: "subscription"`
   - `customer`: existing Stripe customer ID (if returning) or `customer_email` (if new)
   - `line_items`: the selected price
   - `success_url`: `/billing/success?session_id={CHECKOUT_SESSION_ID}`
   - `cancel_url`: `/pricing`
   - `allow_promotion_codes: true`
   - `subscription_data.trial_period_days`: 14 (if eligible for trial; see BL-FR-018)
   - `subscription_data.metadata`: `{ user_id, tier, source }` for tracking
   - `tax_id_collection.enabled: true`
   - `billing_address_collection: "auto"`
4. Backend returns the Checkout Session URL.
5. Frontend redirects user to Stripe-hosted checkout.
6. On success, Stripe redirects to success URL; webhook confirms subscription creation.

**Error handling:**
- If user already has an active subscription: return `409 Conflict` with message "You already have an active subscription. Use the billing portal to change plans."
- If price ID is invalid: return `400 Bad Request`.
- If Stripe API is unavailable: return `503 Service Unavailable` with retry guidance.

#### BL-FR-003: Stripe Customer Portal

The system SHALL integrate Stripe Customer Portal for self-service billing management.

**Portal capabilities:**
- Update payment method (credit/debit card)
- View and download invoices and receipts
- Change subscription plan (upgrade/downgrade)
- Switch billing interval (monthly to annual and vice versa)
- Cancel subscription
- View upcoming invoice preview
- Update billing address

**Implementation:**
- Portal configuration SHALL be created via Stripe Dashboard.
- `POST /api/billing/portal` endpoint creates a portal session and returns the URL.
- Portal sessions are scoped to the authenticated user's Stripe customer ID.
- Return URL after portal actions: `/settings/billing`.
- Portal SHALL be configured with these allowed actions:
  - `subscription_update` with proration behavior `create_prorations`
  - `subscription_cancel` with mode `at_period_end`
  - `payment_method_update` enabled
  - `invoice_history` enabled

#### BL-FR-004: Payment Method Management

The system SHALL manage payment methods via Stripe.

**Requirements:**
- Users can add, update, and remove payment methods through the Customer Portal (BL-FR-003).
- The system SHALL store only the Stripe customer ID and default payment method's last 4 digits + brand (for display purposes) in the local database. No raw card data ever touches TrendEdge servers.
- The `users` table SHALL include:
  - `stripe_customer_id` (varchar, nullable, unique)
  - `payment_method_last4` (varchar(4), nullable)
  - `payment_method_brand` (varchar(20), nullable)
- On `payment_method.attached` and `payment_method.detached` webhooks, update the local cache of payment method display info.
- The billing settings page SHALL display: card brand icon, last 4 digits, expiration month/year, and a "Manage" button linking to the Customer Portal.

---

### 3.2 Subscription Lifecycle

#### BL-FR-005: Free Tier (No Payment Required)

The system SHALL provide full Free tier access without requiring payment information.

**Requirements:**
- New user registration creates a user with `subscription_tier: "free"` and `subscription_status: "active"`.
- No Stripe customer object is created until the user initiates a paid action (checkout or trial).
- Free tier users see an upgrade prompt (non-blocking) when they approach or hit tier limits.
- Free tier has no expiration — users can remain on Free indefinitely.
- Free tier limits are enforced by the feature gating engine (BL-FR-012).

#### BL-FR-006: Upgrade Flow

The system SHALL support upgrades from any tier to a higher tier.

**Upgrade paths:**
- Free -> Trader, Free -> Pro, Free -> Team
- Trader -> Pro, Trader -> Team
- Pro -> Team

**Upgrade behavior:**
1. **Free to Paid:** Redirect to Stripe Checkout (BL-FR-002). On successful payment, tier is updated immediately via webhook.
2. **Paid to Higher Paid:** Process via Stripe Customer Portal or API.
   - Proration: immediately charge the prorated difference for the remainder of the current billing cycle.
   - New tier access: granted immediately upon successful proration charge.
   - If proration charge fails: upgrade is not applied; user remains on current tier; notification sent to user.
3. **Billing interval preserved:** If user is on Trader Monthly and upgrades to Pro, they remain on monthly billing unless they explicitly choose to switch.

**UI flow:**
1. User clicks "Upgrade" on pricing page or from a feature gate prompt.
2. System displays comparison: current plan vs. target plan, highlighting new features.
3. For paid-to-paid: display prorated cost preview ("You'll be charged $XX.XX today for the remainder of this billing period").
4. User confirms; system processes upgrade.
5. On success: confetti animation (brief), confirmation message, immediate access to new features.
6. Dashboard updates to reflect new tier badge.

#### BL-FR-007: Downgrade Flow with Grace Period

The system SHALL support downgrades from any paid tier to a lower tier.

**Downgrade paths:**
- Team -> Pro, Team -> Trader, Team -> Free
- Pro -> Trader, Pro -> Free
- Trader -> Free

**Downgrade behavior:**
1. Downgrade takes effect at the **end of the current billing period** (not immediately). This is the grace period.
2. User retains full access to their current tier features until the period ends.
3. System records a `pending_downgrade` state with `downgrade_to_tier` and `downgrade_effective_date`.
4. At period end, Stripe updates the subscription; webhook triggers local tier change.
5. No refund is issued for the remaining period (user has already paid and retains access).

**Data handling on downgrade:**
- Historical trade data, journal entries, and analytics are **never deleted** on downgrade.
- Features exceeding the new tier limits become read-only:
  - Excess playbooks: visible but cannot create new ones until within limit.
  - Excess broker connections: existing connections preserved but cannot add new ones. Orders from excess connections are rejected with a clear message.
  - Excess instruments: trendline monitoring continues on the most recently active instruments up to the new limit; remainder paused.
- AI-generated trade reviews remain accessible in the journal but new AI reviews are gated.

**UI flow:**
1. User clicks "Change Plan" in billing settings.
2. System shows impact analysis: "You will lose access to: [list of features]. Your data will be preserved."
3. User confirms downgrade.
4. Banner displayed: "Your plan will change to [tier] on [date]. You have full access until then."
5. Downgrade can be cancelled at any time before the effective date.

#### BL-FR-008: Cancellation Flow with Retention Offers

The system SHALL implement a cancellation flow designed to reduce churn while respecting user intent.

**Cancellation flow:**

1. **Step 1 — Reason survey:** User selects a cancellation reason:
   - Too expensive
   - Not using it enough
   - Missing features I need
   - Switching to a competitor
   - Technical issues
   - Temporary pause (will return)
   - Other (free text)

2. **Step 2 — Retention offer** (conditional on reason):

   | Reason | Offer |
   |---|---|
   | Too expensive | "Would a 25% discount for 3 months help? That's [tier] for $XX/mo." Apply coupon `retention_25pct_3mo` if accepted. |
   | Not using it enough | "Switch to a lower plan? [comparison table]" Link to downgrade flow. |
   | Missing features | "Tell us what you need — we prioritize by user feedback." Link to feature request form. |
   | Temporary pause | "Pause your subscription for up to 3 months instead?" Trigger pause flow (BL-FR-009). |
   | Other reasons | "We're sorry to see you go. Your data will be preserved for 90 days if you'd like to return." |

3. **Step 3 — Confirmation:** If user declines the retention offer:
   - Cancellation takes effect at end of current billing period.
   - User retains access until period end.
   - Confirmation email sent with: cancellation date, data retention period (90 days), reactivation instructions.
   - Subscription status set to `cancelling`.

4. **Post-cancellation:**
   - After billing period ends: subscription status set to `cancelled`, tier reverts to `free`.
   - User data retained for 90 days.
   - At 90 days: send "final reminder" email. At 120 days: data deletion per privacy policy.
   - Cancellation can be reversed any time before the period ends.

**Metrics tracking:**
- Log cancellation reason, whether retention offer was shown, whether it was accepted.
- Track retention offer acceptance rate per reason category.

#### BL-FR-009: Subscription Pause

The system SHALL support pausing subscriptions for up to 3 months.

**Pause behavior:**
- Pausing sets `pause_collection` on the Stripe subscription with `behavior: "void"` (no invoices generated during pause).
- Maximum pause duration: 3 months (90 days).
- During pause: user access reverts to Free tier limits.
- User can resume at any time; the billing cycle restarts from the resume date.
- If pause expires without manual resume: subscription automatically resumes and billing restarts.
- Pause counts toward the subscription period for annual plans (pausing does not extend the annual term).

#### BL-FR-010: Reactivation Flow

The system SHALL allow cancelled users to reactivate their subscription.

**Reactivation scenarios:**

| Scenario | Behavior |
|---|---|
| Cancel pending (before period end) | Reverse cancellation via Stripe API. Subscription continues uninterrupted. No new charge. |
| Recently cancelled (<90 days) | Redirect to Checkout with previous tier pre-selected. On success, restore previous tier immediately. Historical data intact. |
| Long-cancelled (>90 days) | Standard new subscription flow. Data may have been deleted per retention policy; user is informed. |

**Implementation:**
- `POST /api/billing/reactivate` checks subscription status and routes to the appropriate flow.
- Reactivation email sent confirming plan, next billing date, and restored access.

#### BL-FR-011: Annual vs. Monthly Billing Toggle

The system SHALL support switching between monthly and annual billing.

**Monthly to Annual:**
- Switch takes effect immediately.
- Stripe prorates: credit remaining monthly period, charge annual price.
- Net charge shown to user before confirmation: "You'll be charged $XXX.XX today (annual price minus $XX.XX credit for remaining days)."
- Annual discount highlighted: "Save XX% with annual billing."

**Annual to Monthly:**
- Switch takes effect at the end of the current annual period.
- No partial refund of annual payment.
- User retains access for the remainder of the annual term.
- After annual period ends, monthly billing begins.

**Implementation:**
- Billing interval change is processed as a subscription update in Stripe with `proration_behavior: "create_prorations"` for upgrades, `proration_behavior: "none"` for downgrades to monthly (deferred).

---

### 3.3 Feature Gating Engine

#### BL-FR-012: Real-Time Tier Checking Middleware

The system SHALL enforce feature access based on the user's current subscription tier.

**Middleware implementation:**
- FastAPI middleware on all protected endpoints checks the user's `subscription_tier` and `subscription_status`.
- The middleware reads tier data from a cached user session (Redis) — not from the database on every request.
- Cache TTL: 60 seconds. Cache is invalidated immediately on tier change (via webhook handler).
- Middleware attaches `request.state.tier` and `request.state.tier_limits` to the request context.
- Endpoints that require tier checking use a decorator: `@requires_tier(minimum="trader")` or `@check_limit("instruments_count")`.

**Tier hierarchy (for comparison):**
```
free (0) < trader (1) < pro (2) < team (3)
```

**Middleware response on access denial:**
```json
{
  "error": "tier_limit_exceeded",
  "message": "This feature requires the Pro plan or higher.",
  "current_tier": "trader",
  "required_tier": "pro",
  "upgrade_url": "/pricing?highlight=pro",
  "limit_detail": null
}
```

HTTP status: `403 Forbidden` for tier-blocked features, `429 Too Many Requests` for usage limits exceeded within the tier.

#### BL-FR-013: Feature Flag System Tied to Subscription Tier

The system SHALL maintain a feature flag registry mapping features to tier requirements.

**Feature flag registry:**

| Feature Key | Free | Trader | Pro | Team | Limit Type |
|---|---|---|---|---|---|
| `trendline.detection` | yes | yes | yes | yes | instrument_count |
| `trendline.realtime` | no | yes | yes | yes | boolean |
| `trendline.custom_params` | no | no | no | yes | boolean |
| `execution.live` | no | yes | yes | yes | boolean |
| `execution.paper` | yes | yes | yes | yes | boolean |
| `execution.broker_count` | 0 | 1 | 3 | unlimited | numeric |
| `execution.account_count` | 0 | 1 | 5 | unlimited | numeric |
| `journal.monthly_limit` | 10 | unlimited | unlimited | unlimited | numeric |
| `journal.ai_review` | no | no | yes | yes | boolean |
| `journal.sharing` | no | no | no | yes | boolean |
| `playbook.custom_count` | 0 | 5 | unlimited | unlimited | numeric |
| `playbook.templates` | no | no | no | yes | boolean |
| `analytics.basic` | yes | yes | yes | yes | boolean |
| `analytics.full_dashboard` | no | yes | yes | yes | boolean |
| `analytics.advanced` | no | no | yes | yes | boolean |
| `analytics.monte_carlo` | no | no | yes | yes | boolean |
| `analytics.team` | no | no | no | yes | boolean |
| `notifications.email` | yes | yes | yes | yes | boolean |
| `notifications.telegram` | no | yes | yes | yes | boolean |
| `notifications.all_channels` | no | no | yes | yes | boolean |
| `notifications.custom_hooks` | no | no | no | yes | boolean |
| `ai.conversational` | no | no | yes | yes | boolean |
| `ai.trade_review` | no | no | yes | yes | boolean |
| `support.priority` | no | no | yes | yes | boolean |
| `support.dedicated` | no | no | no | yes | boolean |

**Implementation:**
- Feature flags stored in a `tier_features` configuration table or YAML configuration file.
- Loaded into Redis on application startup and on configuration changes.
- Feature check function: `has_feature(user_id, feature_key) -> bool` and `get_limit(user_id, feature_key) -> int | None`.
- Configuration changes require a deployment (not runtime-editable by default), preventing accidental tier changes.

#### BL-FR-014: Graceful Degradation on Limit Exceeded

The system SHALL degrade gracefully when users hit tier limits, using soft blocks and clear messaging rather than hard errors.

**Degradation behaviors by feature:**

| Feature | At Limit Behavior | Message |
|---|---|---|
| Instruments (Free: 3) | Cannot add new instruments; existing continue. Show upgrade prompt inline. | "You're monitoring 3 of 3 instruments. Upgrade to Trader for up to 10." |
| Instruments (Trader: 10) | Same pattern. | "You're monitoring 10 of 10 instruments. Upgrade to Pro for unlimited." |
| Journal trades (Free: 10/mo) | Trade still executes; journal entry created but marked as "over limit". Visible but read-only until upgrade or next month. | "You've reached 10 journal entries this month. Upgrade to Trader for unlimited journaling, or wait until [next month date]." |
| Playbooks (Trader: 5) | Cannot create new; existing continue to function. | "You have 5 of 5 custom playbooks. Upgrade to Pro for unlimited playbooks." |
| Broker connections | Cannot add new broker; existing connections continue working. | "You're using 1 of 1 broker connection. Upgrade to Pro to connect up to 3 brokers." |
| AI features | Feature button/section visible but disabled with lock icon and upgrade CTA. | "AI Trade Review is available on Pro and above. Upgrade to unlock AI-powered insights." |

**Design principles:**
- Never interrupt an active trade due to a tier limit.
- Never silently fail — always show a clear message explaining the limit and how to resolve it.
- Upgrade CTAs link directly to the pricing page with the recommended tier pre-highlighted.
- Usage counters visible in the UI: "3/10 instruments used", "8/10 journal entries this month".

#### BL-FR-015: Usage Tracking

The system SHALL track feature usage for enforcement of tier limits and analytics.

**Tracked metrics:**

| Metric | Tracked Per | Storage | Reset Cycle |
|---|---|---|---|
| Journal entries created | user, month | PostgreSQL `usage_tracking` table | Monthly (calendar month) |
| Active instruments monitored | user | PostgreSQL, real-time count | None (running count) |
| Active broker connections | user | PostgreSQL, real-time count | None (running count) |
| Active accounts per broker | user, broker | PostgreSQL, real-time count | None (running count) |
| Custom playbooks created | user | PostgreSQL, real-time count | None (running count) |
| AI feature invocations | user, month | PostgreSQL `usage_tracking` table | Monthly |
| Claude API tokens consumed | user, month | PostgreSQL `usage_tracking` table | Monthly |

**`usage_tracking` table schema:**

| Column | Type | Description |
|---|---|---|
| id | bigint | Primary key |
| user_id | uuid | Foreign key to users |
| metric_key | varchar(50) | e.g., `journal_entries`, `ai_invocations` |
| period_start | date | First day of the tracking period |
| period_end | date | Last day of the tracking period |
| current_value | integer | Current count for this period |
| limit_value | integer | Tier limit for this metric (null = unlimited) |
| created_at | timestamptz | Record creation |
| updated_at | timestamptz | Last update |

**Unique constraint:** `(user_id, metric_key, period_start)`

**Implementation:**
- Usage increments are atomic (`UPDATE ... SET current_value = current_value + 1`).
- Usage checks read from Redis cache (populated on first check per period, invalidated on increment).
- Monthly counters reset automatically via a scheduled job on the 1st of each month at 00:00 UTC.
- Usage data is retained for 12 months for analytics purposes, then aggregated and archived.

---

### 3.4 Webhook Handling

#### BL-FR-016: Stripe Webhook Receiver

The system SHALL receive and process Stripe webhook events for subscription and payment lifecycle management.

**Endpoint:** `POST /api/webhooks/stripe`

**Handled events:**

| Stripe Event | Action |
|---|---|
| `checkout.session.completed` | Create/link Stripe customer; activate subscription; update user tier; send welcome email. |
| `customer.subscription.created` | Set subscription status to `active`; update tier; log event. |
| `customer.subscription.updated` | Handle plan change, billing interval change, or status change. Update local subscription record. |
| `customer.subscription.deleted` | Set tier to `free`; set status to `cancelled`; send cancellation confirmation email. |
| `customer.subscription.paused` | Set status to `paused`; revert to Free tier limits. |
| `customer.subscription.resumed` | Restore tier; set status to `active`. |
| `customer.subscription.trial_will_end` | Send email 3 days before trial ends: "Your Pro trial ends on [date]. Add a payment method to continue." |
| `invoice.payment_succeeded` | Update `last_payment_date`; reset any dunning state; send receipt email. |
| `invoice.payment_failed` | Trigger dunning sequence (BL-FR-020); update payment status. |
| `invoice.finalized` | Store invoice ID and PDF URL for user access. |
| `payment_method.attached` | Update cached payment method display info. |
| `payment_method.detached` | Clear cached payment method display info if it was the default. |
| `customer.updated` | Sync billing email, name, or address changes. |

**Unhandled events:** Log to monitoring with event type for future analysis. Do not error on unknown event types.

#### BL-FR-017: Webhook Signature Verification

The system SHALL verify the authenticity of all incoming Stripe webhooks.

**Implementation:**
- Use `stripe.Webhook.construct_event()` with the raw request body and `STRIPE_WEBHOOK_SECRET` environment variable.
- Reject requests with invalid signatures: return `400 Bad Request` (do not reveal reason details).
- Reject requests with timestamps older than 5 minutes (Stripe's tolerance): return `400 Bad Request`.
- `STRIPE_WEBHOOK_SECRET` stored in environment variables, never in source code or configuration files.
- Separate webhook secrets for test mode and live mode.

#### BL-FR-018: Idempotent Event Processing

The system SHALL process each webhook event exactly once, even if Stripe delivers it multiple times.

**Implementation:**
- Store processed event IDs in a `stripe_events` table:

  | Column | Type | Description |
  |---|---|---|
  | event_id | varchar(255) | Stripe event ID (primary key) |
  | event_type | varchar(100) | e.g., `invoice.payment_succeeded` |
  | processed_at | timestamptz | When the event was processed |
  | status | varchar(20) | `processed`, `failed`, `skipped` |
  | error_message | text | Error details if processing failed |
  | raw_payload | jsonb | Full event payload for debugging |

- Before processing: check if `event_id` exists in the table.
  - If exists with `status = processed`: return `200 OK` immediately (idempotent skip).
  - If exists with `status = failed`: re-attempt processing (retry logic).
  - If not exists: insert with `status = processing`, process event, update to `processed` or `failed`.
- Use database transaction to ensure atomicity of the insert + processing.
- Retain processed events for 90 days, then archive.

#### BL-FR-019: Failed Payment Retry Handling

The system SHALL handle failed payment retries per Stripe's Smart Retries configuration.

**Stripe retry configuration:**
- Enable Stripe Smart Retries (ML-optimized retry timing).
- Maximum retry attempts: 4 over 3 weeks.
- After all retries exhausted: cancel subscription.

**Local handling:**
- On `invoice.payment_failed`: check `attempt_count` from the invoice object.
- Track payment failure state in the local `subscriptions` table: `payment_status` field (`current`, `past_due`, `unpaid`).
- Do not immediately restrict access on first failure (grace period of 7 days).
- After 7 days past due: restrict to Free tier limits but maintain data access.
- After subscription cancelled by Stripe (all retries exhausted): full downgrade to Free tier.

#### BL-FR-020: Dunning Management

The system SHALL implement an email sequence for failed payments to maximize recovery.

**Dunning email sequence:**

| Trigger | Timing | Email Content |
|---|---|---|
| First payment failure | Immediately | "Your payment of $XX failed. Please update your payment method to avoid service interruption." CTA: "Update Payment Method" -> Customer Portal. |
| Second failure (Stripe retry) | ~3 days after first | "We're still unable to process your payment. Your access will be limited on [date, 7 days from first failure]." CTA: "Update Payment Method". |
| Grace period ending | 6 days after first failure | "Action required: Update your payment method by tomorrow to maintain your [tier] access." Urgent tone. CTA: "Update Payment Method". |
| Access restricted | 7 days after first failure | "Your account has been restricted to Free tier access. Update your payment method to restore full access immediately." CTA: "Restore Access". |
| Final warning | 3 days before cancellation | "Your subscription will be cancelled on [date]. All Pro/Team features will be permanently removed. Your data will be preserved for 90 days." CTA: "Keep My Subscription". |
| Subscription cancelled | On cancellation | "Your subscription has been cancelled. Your data will be preserved for 90 days. You can reactivate anytime." CTA: "Reactivate". |

**Implementation:**
- Dunning emails sent via the notification service (SendGrid).
- Each email in the sequence is tracked to prevent duplicates.
- Dunning state stored in `subscriptions` table: `dunning_step` (0-5), `dunning_started_at`.
- Dunning state reset when payment succeeds (via `invoice.payment_succeeded` webhook).

---

### 3.5 Invoice and Receipt Management

#### BL-FR-021: Invoice Access

The system SHALL provide users access to their billing history, invoices, and receipts.

**Requirements:**
- Billing history page at `/settings/billing/history` displays all invoices.
- Each invoice row shows: date, description, amount, status (paid, open, void, uncollectible), and a download link.
- Invoice PDF URLs are retrieved from Stripe's `invoice.invoice_pdf` field and cached locally.
- Invoices are accessible via the Stripe Customer Portal (BL-FR-003) as well.
- The system stores invoice metadata in a local `invoices` table for fast retrieval:

  | Column | Type | Description |
  |---|---|---|
  | id | bigint | Primary key |
  | user_id | uuid | Foreign key to users |
  | stripe_invoice_id | varchar(255) | Stripe invoice ID |
  | amount_paid | integer | Amount in cents |
  | currency | varchar(3) | Always `usd` |
  | status | varchar(20) | `paid`, `open`, `void`, `uncollectible` |
  | invoice_pdf_url | text | URL to Stripe-hosted PDF |
  | period_start | timestamptz | Billing period start |
  | period_end | timestamptz | Billing period end |
  | created_at | timestamptz | Invoice creation date |

- Invoices are synced from Stripe via webhooks (`invoice.finalized`, `invoice.payment_succeeded`).

---

### 3.6 Usage Metering for AI Features

#### BL-FR-022: Claude API Cost Tracking

The system SHALL track and meter Claude API usage per user to manage costs and enforce fair use.

**AI features consuming Claude API:**
- Conversational analytics (Pro, Team)
- Trade review assistant (Pro, Team)
- AI-powered journal review (Pro, Team)

**Metering implementation:**
- Each Claude API call logs: `user_id`, `feature_key`, `model`, `input_tokens`, `output_tokens`, `estimated_cost_usd`, `timestamp`.
- Storage: `ai_usage_log` table.

  | Column | Type | Description |
  |---|---|---|
  | id | bigint | Primary key |
  | user_id | uuid | Foreign key to users |
  | feature_key | varchar(50) | `conversational_analytics`, `trade_review`, `journal_review` |
  | model | varchar(50) | e.g., `claude-sonnet-4-20250514` |
  | input_tokens | integer | Tokens in the prompt |
  | output_tokens | integer | Tokens in the response |
  | estimated_cost_usd | decimal(10,6) | Estimated cost based on current pricing |
  | created_at | timestamptz | Timestamp of the API call |

**Fair use limits (soft caps):**

| Tier | Monthly AI Calls | Monthly Token Budget |
|---|---|---|
| Free | 0 | 0 |
| Trader | 0 | 0 |
| Pro | 100 calls | 500K tokens |
| Team | 500 calls | 2.5M tokens |

- When a user reaches 80% of their AI budget: show a warning in the UI.
- When a user reaches 100%: AI features show "You've used your AI budget for this month. Resets on [date]." No overage charges at launch.
- Admin dashboard shows per-user AI costs, aggregate monthly costs, and cost-per-feature breakdown.

---

### 3.7 Trial Period Support

#### BL-FR-023: 14-Day Pro Trial

The system SHALL offer a 14-day free trial of the Pro tier to new users.

**Trial eligibility:**
- Available only to users who have never had a paid subscription or trial.
- One trial per account (tracked via `has_used_trial` boolean on the user record).
- Trial requires a payment method on file (collected via Stripe Checkout with `trial_period_days: 14`).

**Trial behavior:**
- During trial: full Pro tier access.
- Trial start: upon completing Checkout with trial.
- Trial end: 14 days after start, at which point:
  - If payment method is valid: automatic conversion to paid Pro subscription. Send email: "Your trial has ended and your Pro subscription is now active. You've been charged $99.00."
  - If payment method fails: subscription enters dunning flow (BL-FR-020). Grace period applies.
- Trial can be cancelled at any time during the 14 days. If cancelled:
  - Access remains Pro until trial end date.
  - No charge is made.
  - User reverts to Free tier after trial end.

**Trial notifications:**

| Timing | Notification |
|---|---|
| Trial start | "Welcome to your 14-day Pro trial! Here's what you can do..." |
| Day 7 | "You're halfway through your Pro trial. Here's what you've accomplished so far: [usage summary]." |
| Day 11 (3 days before end) | "Your Pro trial ends in 3 days. Your card ending in XXXX will be charged $99/mo. Cancel anytime before [date]." (Triggered by `customer.subscription.trial_will_end` webhook.) |
| Trial ends (auto-convert) | "Your trial has ended. Welcome to TrendEdge Pro!" |
| Trial ends (cancelled) | "Your Pro trial has ended. You're now on the Free plan. Upgrade anytime to get Pro features back." |

---

### 3.8 Coupon and Promotion Code Support

#### BL-FR-024: Coupon Management

The system SHALL support Stripe coupons and promotion codes.

**Coupon types:**

| Type | Example | Configuration |
|---|---|---|
| Percentage off | 25% off for 3 months | `percent_off: 25`, `duration: repeating`, `duration_in_months: 3` |
| Fixed amount off | $20 off first month | `amount_off: 2000`, `duration: once` |
| Forever discount | 15% off forever | `percent_off: 15`, `duration: forever` |

**Promotion code features:**
- Codes are human-readable strings (e.g., `LAUNCH25`, `TRADERLIFE`, `RETENTION25`).
- Configurable restrictions: minimum tier, maximum redemptions, expiration date, first-time customers only.
- Promotion codes are created via admin dashboard or Stripe Dashboard.
- Users can apply promotion codes during Stripe Checkout (`allow_promotion_codes: true`).
- Users can apply promotion codes post-checkout via the Customer Portal.

**Admin management:**
- Admin panel at `/admin/promotions` lists all active coupons and promotion codes.
- Each entry shows: code, discount details, redemption count, expiration, status.
- Admin can create new codes, deactivate existing codes, and view redemption history.

**System-generated coupons:**
- `retention_25pct_3mo`: 25% off for 3 months, used in cancellation retention flow (BL-FR-008).
- `annual_switch_10pct`: 10% off first year, used to incentivize monthly-to-annual switches.
- `referral_1mo_free`: 1 month free, used in future referral program.

---

### 3.9 Revenue Analytics Dashboard (Admin)

#### BL-FR-025: Revenue Metrics Dashboard

The system SHALL provide an admin dashboard displaying key revenue and subscription metrics.

**Dashboard location:** `/admin/revenue`

**Metrics displayed:**

| Category | Metrics |
|---|---|
| Revenue | MRR (Monthly Recurring Revenue), ARR, total revenue (MTD, QTD, YTD), revenue by tier, revenue by billing interval |
| Subscriptions | Total active subscriptions, subscriptions by tier, new subscriptions (this period), churned subscriptions (this period) |
| Churn | Monthly churn rate (%), churn by tier, churn by reason (from cancellation survey), net revenue churn |
| Growth | Net new MRR, expansion MRR (upgrades), contraction MRR (downgrades), churned MRR |
| Trials | Active trials, trial-to-paid conversion rate, trial cancellation rate |
| Payments | Successful payments (count, $), failed payments (count, $), recovery rate, average revenue per user |
| AI Costs | Total Claude API costs, cost per user, cost by feature, margin impact |
| Coupons | Active promotions, total discount given, redemption counts |

**Visualization:**
- MRR trend chart (line, 12-month rolling)
- Subscription distribution (stacked bar by tier)
- Churn cohort analysis (heatmap)
- Revenue waterfall (new + expansion - contraction - churn)
- Trial funnel (started -> converted -> churned)

**Data source:**
- Metrics calculated from local `subscriptions`, `invoices`, `usage_tracking`, and `ai_usage_log` tables.
- Dashboard refreshes every 15 minutes via a background job.
- Historical metrics stored in a `revenue_metrics_daily` table for trend analysis.

**Access control:**
- Admin-only (requires `admin` role from PRD-008 Auth).
- Audit log for dashboard access.

---

### 3.10 Refund Processing

#### BL-FR-026: Refund Policy and Processing

The system SHALL support processing refunds through an admin interface.

**Refund policy:**
- Full refund within 7 days of initial subscription purchase (no questions asked).
- Pro-rated refund at admin discretion for annual subscribers within 30 days.
- No automatic refunds; all refunds require admin approval.
- Refunds for the current billing period only; past periods are not refundable.

**Admin refund flow:**
1. Admin navigates to user's billing page in admin panel.
2. Admin selects the invoice to refund.
3. Admin chooses: full refund or partial refund (specify amount).
4. Admin enters a reason for the refund (required).
5. System processes refund via Stripe API (`stripe.Refund.create()`).
6. On success: update local invoice status to `refunded`; log refund in `refunds` table; notify user via email ("You've been issued a refund of $XX.XX. It may take 5-10 business days to appear on your statement.").
7. Refund does NOT automatically cancel the subscription. Admin must separately cancel if needed.

**`refunds` table schema:**

| Column | Type | Description |
|---|---|---|
| id | bigint | Primary key |
| user_id | uuid | Foreign key to users |
| stripe_refund_id | varchar(255) | Stripe refund ID |
| stripe_invoice_id | varchar(255) | Original invoice ID |
| amount | integer | Refund amount in cents |
| reason | text | Admin-provided reason |
| processed_by | uuid | Admin user ID |
| created_at | timestamptz | Refund timestamp |

---

### 3.11 Subscription Data Model

#### BL-FR-027: Subscriptions Table

The system SHALL maintain a local `subscriptions` table synchronized with Stripe.

**`subscriptions` table schema:**

| Column | Type | Description |
|---|---|---|
| id | bigint | Primary key |
| user_id | uuid | Foreign key to users (unique) |
| stripe_subscription_id | varchar(255) | Stripe subscription ID (nullable for Free) |
| stripe_customer_id | varchar(255) | Stripe customer ID (nullable for Free) |
| tier | varchar(20) | `free`, `trader`, `pro`, `team` |
| status | varchar(20) | `active`, `trialing`, `past_due`, `paused`, `cancelling`, `cancelled` |
| billing_interval | varchar(10) | `monthly`, `annual`, `none` (for Free) |
| current_period_start | timestamptz | Start of current billing period |
| current_period_end | timestamptz | End of current billing period |
| trial_start | timestamptz | Trial start date (nullable) |
| trial_end | timestamptz | Trial end date (nullable) |
| cancel_at_period_end | boolean | Whether cancellation is pending |
| cancelled_at | timestamptz | When cancellation was requested |
| cancellation_reason | varchar(50) | From cancellation survey |
| pending_downgrade_tier | varchar(20) | Tier to downgrade to at period end (nullable) |
| payment_status | varchar(20) | `current`, `past_due`, `unpaid` |
| dunning_step | integer | Current dunning email step (0-5) |
| dunning_started_at | timestamptz | When dunning sequence began |
| has_used_trial | boolean | Whether user has ever used a trial |
| pause_starts_at | timestamptz | Pause start date (nullable) |
| pause_resumes_at | timestamptz | Pause resume date (nullable) |
| created_at | timestamptz | Record creation |
| updated_at | timestamptz | Last update |

**Indexes:**
- `idx_subscriptions_user_id` (unique)
- `idx_subscriptions_stripe_subscription_id` (unique)
- `idx_subscriptions_stripe_customer_id`
- `idx_subscriptions_status`
- `idx_subscriptions_tier`

---

### 3.12 Subscription State Machine

#### BL-FR-028: Subscription State Transitions

The system SHALL enforce valid state transitions for subscriptions.

**Valid states:** `active`, `trialing`, `past_due`, `paused`, `cancelling`, `cancelled`

**State transition table:**

| From State | Event | To State | Actions |
|---|---|---|---|
| (none) | user_registers | active (free) | Create subscription record with `tier: free`, `status: active`. |
| active (free) | checkout_completed | active (paid) | Update tier; set Stripe IDs; send welcome email. |
| active (free) | trial_started | trialing | Update tier to `pro`; set trial dates; send trial welcome email. |
| trialing | trial_ended_payment_success | active (paid) | Update status to `active`; send conversion email. |
| trialing | trial_ended_payment_failed | past_due | Begin dunning sequence. |
| trialing | user_cancels | cancelling | Set `cancel_at_period_end: true`; retain access until trial end. |
| active (paid) | upgrade_completed | active (paid) | Update tier; proration charged; send upgrade confirmation. |
| active (paid) | downgrade_requested | active (paid) | Set `pending_downgrade_tier`; no immediate tier change. |
| active (paid) | billing_interval_changed | active (paid) | Update interval; process proration if applicable. |
| active (paid) | payment_failed | past_due | Set `payment_status: past_due`; begin dunning. |
| active (paid) | user_cancels | cancelling | Set `cancel_at_period_end: true`; retention offer shown. |
| active (paid) | pause_requested | paused | Set pause dates; revert to Free limits; void invoices. |
| past_due | payment_succeeded | active (paid) | Reset dunning state; restore full access. |
| past_due | all_retries_exhausted | cancelled | Cancel subscription; revert to Free tier; send cancellation email. |
| past_due | user_updates_payment | active (paid) | Retry charge; if successful, reset dunning. |
| paused | resume_requested | active (paid) | Resume billing; restore tier. |
| paused | pause_expired | active (paid) | Auto-resume; restart billing cycle. |
| cancelling | period_ends | cancelled | Revert to Free tier; clear Stripe IDs; begin data retention countdown. |
| cancelling | user_reactivates | active (paid) | Remove `cancel_at_period_end`; continue subscription. |
| cancelled | user_resubscribes | active (paid) | New Checkout; create new subscription; restore data if within retention. |

**Invalid transitions SHALL be rejected** with a logged error and a user-facing message explaining why the action cannot be performed.

---

## 4. Non-Functional Requirements

#### BL-NFR-001: Webhook Processing Latency

Stripe webhook events SHALL be acknowledged (HTTP 200 response) within **5 seconds** of receipt.

**Implementation:**
- Webhook handler performs signature verification and idempotency check synchronously.
- Actual event processing (tier updates, email sending, etc.) is dispatched to a background task queue (Celery/Dramatiq).
- The webhook endpoint returns `200 OK` after queuing, not after processing.
- Processing of queued events completes within 30 seconds (p99).

#### BL-NFR-002: Feature Gate Check Latency

Feature gate checks SHALL complete in under **50ms** (p99) per request.

**Implementation:**
- Tier and feature flag data cached in Redis with 60-second TTL.
- Cache key: `user:{user_id}:tier_features`.
- Cache warmed on user login; invalidated on tier change.
- Fallback: if Redis is unavailable, read from PostgreSQL (acceptable latency increase to ~100ms).
- No external API calls (e.g., to Stripe) during feature gate checks.

#### BL-NFR-003: Zero Revenue Leakage

The system SHALL ensure no paying customer accesses features beyond their tier, and no entitled customer is denied features they have paid for.

**Implementation:**
- Tier state is the source of truth: synced from Stripe via webhooks, cached in Redis, verified on every protected request.
- Automated daily reconciliation job compares local subscription records against Stripe API:
  - For each active subscription in the local database, verify it matches Stripe's state.
  - Log discrepancies as `CRITICAL` alerts.
  - Auto-correct local state to match Stripe (Stripe is the source of truth for billing; local DB is the source of truth for feature access).
- Monthly revenue reconciliation report: compare Stripe dashboard revenue against local invoice totals.
- Alerting: PagerDuty alert if reconciliation finds >0 discrepancies.

#### BL-NFR-004: PCI DSS Compliance

The system SHALL maintain PCI DSS compliance by delegating all payment card handling to Stripe.

**Requirements:**
- No credit card numbers, CVVs, or full card data SHALL be transmitted to, processed by, or stored on TrendEdge servers.
- All payment forms use Stripe Checkout (hosted) or Stripe Elements (client-side tokenization).
- The system stores only: Stripe customer ID, last 4 digits of the card, card brand, and expiration (for display only).
- Stripe.js loaded directly from `js.stripe.com` (not self-hosted).
- TrendEdge servers communicate with Stripe only via server-side API using secret keys.
- Annual PCI SAQ-A (Self-Assessment Questionnaire A) completed, documenting that all cardholder data is handled by Stripe.

#### BL-NFR-005: Availability

The billing system SHALL maintain 99.9% uptime for feature gating and 99.5% uptime for payment processing.

**Implementation:**
- Feature gating operates independently of Stripe availability (uses cached tier data).
- If Stripe is unavailable during checkout: show "Payment processing is temporarily unavailable. Please try again in a few minutes."
- If Stripe webhooks are delayed: local tier state continues serving from last known good state; reconciliation catches up.
- Health check endpoint: `GET /api/health/billing` verifies Redis connectivity, database connectivity, and Stripe API reachability.

#### BL-NFR-006: Data Retention

The system SHALL enforce the following data retention policies:

| Data | Retention Period | After Retention |
|---|---|---|
| Active subscription records | Indefinite (while active) | N/A |
| Cancelled subscription records | 7 years (tax/legal) | Archive to cold storage |
| Invoice records | 7 years (tax/legal) | Archive to cold storage |
| Stripe webhook events | 90 days | Delete |
| Usage tracking data | 12 months | Aggregate and archive |
| AI usage logs | 12 months | Aggregate and archive |
| Refund records | 7 years | Archive to cold storage |
| User trade data (after account deletion) | 90 days grace period | Permanent deletion |

#### BL-NFR-007: Scalability

The billing system SHALL support up to 10,000 concurrent subscribers without performance degradation.

**Implementation:**
- Feature gate checks use Redis (single-digit ms latency at 100K+ ops/sec).
- Webhook processing uses a dedicated Celery queue with auto-scaling workers.
- Usage tracking uses atomic PostgreSQL updates (no locking contention).
- Revenue analytics dashboard pre-computes metrics via background jobs (not real-time queries).

---

## 5. Dependencies

### 5.1 Internal Dependencies

| Dependency | PRD | What This PRD Needs |
|---|---|---|
| Infrastructure | PRD-001 | PostgreSQL database, Redis cache, Celery task queue, environment variable management, monitoring (Sentry, Axiom). |
| Auth & User Management | PRD-008 | Authenticated user sessions, user ID for subscription records, admin role for revenue dashboard access, user registration event to trigger Free tier provisioning. |
| Notification Service | PRD-XXX (Notifications) | Email delivery (SendGrid) for dunning emails, trial notifications, receipts. Telegram delivery for payment confirmations. |

### 5.2 External Dependencies

| Dependency | Type | Details |
|---|---|---|
| Stripe API | Payment processor | Stripe API v2023-10-16 or later. Products, Prices, Subscriptions, Checkout Sessions, Customer Portal, Webhooks, Coupons, Refunds. |
| Stripe.js | Client-side SDK | Loaded from `js.stripe.com` for Checkout redirect. |
| Stripe CLI | Development tool | For local webhook testing (`stripe listen --forward-to localhost:8000/api/webhooks/stripe`). |
| SendGrid | Email delivery | Transactional emails for dunning, receipts, trial notifications. |
| Claude API (Anthropic) | AI provider | Metered usage tracked by this billing system. Actual API integration owned by PRD-XXX (AI Features). |

### 5.3 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `STRIPE_SECRET_KEY` | Stripe API secret key (live or test) | Yes |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key for client-side | Yes |
| `STRIPE_WEBHOOK_SECRET` | Webhook endpoint signing secret | Yes |
| `STRIPE_PRICE_TRADER_MONTHLY` | Price ID for Trader monthly | Yes |
| `STRIPE_PRICE_TRADER_ANNUAL` | Price ID for Trader annual | Yes |
| `STRIPE_PRICE_PRO_MONTHLY` | Price ID for Pro monthly | Yes |
| `STRIPE_PRICE_PRO_ANNUAL` | Price ID for Pro annual | Yes |
| `STRIPE_PRICE_TEAM_MONTHLY` | Price ID for Team monthly | Yes |
| `STRIPE_PRICE_TEAM_ANNUAL` | Price ID for Team annual | Yes |
| `STRIPE_PORTAL_CONFIG_ID` | Customer portal configuration ID | Yes |
| `BILLING_TRIAL_DAYS` | Trial period in days (default: 14) | No |
| `BILLING_DUNNING_GRACE_DAYS` | Grace period before access restriction (default: 7) | No |
| `BILLING_DATA_RETENTION_DAYS` | Days to retain cancelled user data (default: 90) | No |

---

## 6. Testing Requirements

### 6.1 Stripe Test Mode End-to-End Testing

**BL-TEST-001:** All development and staging environments SHALL use Stripe test mode with test API keys.

**Test scenarios:**

| Test Case | Stripe Test Card | Expected Result |
|---|---|---|
| Successful checkout | `4242 4242 4242 4242` | Subscription created, tier updated, welcome email sent. |
| Card declined | `4000 0000 0000 0002` | Checkout fails, user shown error, no subscription created. |
| Insufficient funds | `4000 0000 0000 9995` | Payment fails, dunning sequence initiated. |
| 3D Secure required | `4000 0025 0000 3155` | 3DS challenge presented, subscription created on completion. |
| Card expires during subscription | `4000 0000 0000 0341` | Renewal fails, dunning email sent, grace period starts. |
| Disputed payment | `4000 0000 0000 0259` | Dispute webhook received, admin alerted. |

**Test automation:**
- Integration tests use Stripe test mode API directly (not mocks) for checkout, subscription changes, and webhook delivery.
- Webhook tests use Stripe CLI (`stripe trigger`) or construct test events programmatically.
- CI/CD pipeline runs billing integration tests on every PR that touches billing code.

### 6.2 Webhook Signature Verification Testing

**BL-TEST-002:** Webhook security SHALL be tested for both valid and invalid scenarios.

| Test Case | Expected Result |
|---|---|
| Valid signature, valid payload | Event processed successfully, `200 OK`. |
| Invalid signature | Rejected with `400 Bad Request`, event not processed. |
| Missing signature header | Rejected with `400 Bad Request`. |
| Expired timestamp (>5 min old) | Rejected with `400 Bad Request`. |
| Valid signature, malformed payload | Rejected with `400 Bad Request`, error logged. |
| Replay attack (duplicate event ID) | Idempotent skip, `200 OK`, no duplicate processing. |

### 6.3 Subscription Lifecycle State Machine Testing

**BL-TEST-003:** Every valid state transition in BL-FR-028 SHALL have at least one automated test.

**Test coverage requirements:**
- All 20+ state transitions from the state machine table tested.
- Invalid transitions tested to confirm they are rejected.
- Concurrent state change attempts tested (e.g., user cancels while payment is processing).
- Edge case: subscription expires exactly at billing period boundary.
- Edge case: upgrade and downgrade within the same billing period.
- Edge case: cancel and reactivate multiple times.

### 6.4 Feature Gating Across All Tier Combinations

**BL-TEST-004:** Feature access SHALL be tested for every feature/tier combination.

**Test matrix:**

For each of the 25+ feature keys in BL-FR-013, verify:
- Free tier: correct access (enabled/disabled per matrix).
- Trader tier: correct access.
- Pro tier: correct access.
- Team tier: correct access.
- Transition: feature access changes immediately on upgrade.
- Transition: feature access changes at period end on downgrade.
- Cache invalidation: feature access updates within 60 seconds of tier change.

**Automated test approach:**
- Parameterized tests iterating over the feature flag registry.
- Each test: set user to a specific tier, check each feature, assert expected access.
- Total test cases: ~100 (25 features x 4 tiers).

### 6.5 Proration Calculation Verification

**BL-TEST-005:** Proration amounts SHALL be verified for accuracy.

| Scenario | Verification |
|---|---|
| Trader Monthly -> Pro Monthly at mid-cycle (day 15 of 30) | Credit: ~$24.50, Charge: ~$49.50. Net: ~$25.00. |
| Pro Monthly -> Team Monthly at day 1 | Credit: ~$99.00, Charge: ~$199.00. Net: ~$100.00. |
| Pro Monthly -> Team Monthly at day 29 of 30 | Credit: ~$3.30, Charge: ~$6.63. Net: ~$3.33. |
| Monthly -> Annual switch | Credit remaining monthly amount, charge full annual. |

**Note:** Exact proration is calculated by Stripe. Tests verify that the Stripe proration preview matches expectations within $0.01 tolerance.

### 6.6 Failed Payment Handling Testing

**BL-TEST-006:** The dunning sequence SHALL be tested end-to-end.

| Step | Test Verification |
|---|---|
| First failure | Dunning email 1 sent; `payment_status` set to `past_due`; user retains full access. |
| Second failure (retry) | Dunning email 2 sent; `dunning_step` incremented. |
| Grace period (7 days) | Access restricted to Free tier; dunning email 4 sent. |
| Payment recovery | Card updated; payment succeeds; full access restored; dunning reset. |
| All retries exhausted | Subscription cancelled; user on Free tier; cancellation email sent. |

### 6.7 Idempotency Testing

**BL-TEST-007:** Duplicate webhook delivery SHALL not cause duplicate processing.

| Test Case | Expected Result |
|---|---|
| Same event delivered twice | Second delivery returns `200 OK`; no duplicate side effects (no duplicate emails, no duplicate tier changes). |
| Same event delivered 10 times rapidly | All return `200 OK`; exactly one processing occurs. |
| Event with same ID but different payload (tampered) | Rejected — signature verification fails. |
| Event processing fails on first attempt, retried | Second attempt processes successfully; final state is correct. |

### 6.8 Load Testing

**BL-TEST-008:** The billing system SHALL be load tested for expected peak scenarios.

| Scenario | Target | Metric |
|---|---|---|
| Feature gate checks | 1,000 concurrent users | p99 < 50ms |
| Webhook burst (e.g., batch renewal) | 100 events/second | All processed within 30s, zero drops |
| Checkout session creation | 50 concurrent sessions | All created within 2s |
| Revenue dashboard query | 10,000 subscriptions | Page load < 3s |

---

## 7. Security

### 7.1 Stripe Webhook Signatures

- All webhook requests verified using Stripe's HMAC-SHA256 signature scheme (BL-FR-017).
- Webhook signing secret rotated annually or immediately upon suspected compromise.
- Webhook endpoint is public (no auth required) but protected by signature verification.
- Rate limiting on the webhook endpoint: 100 requests/second (to prevent DoS).

### 7.2 No PCI Data Stored

- TrendEdge is classified as **PCI SAQ-A** (all cardholder data handled by Stripe).
- No card numbers, CVVs, or full expiration dates stored in any database, log, cache, or file.
- Payment forms use Stripe Checkout (hosted pages) — card data never transits TrendEdge servers.
- Stripe API secret keys stored in environment variables, never in source code.
- Stripe API requests made over HTTPS only.

### 7.3 Secure Customer Portal

- Customer Portal sessions are created server-side with the authenticated user's Stripe customer ID.
- Portal session URLs are single-use and expire after 24 hours.
- Portal access requires active authentication in TrendEdge (cannot be accessed without logging in first).
- The portal return URL is validated to be a TrendEdge domain.

### 7.4 API Security

- All billing API endpoints require authentication (JWT from PRD-008).
- Admin billing endpoints require `admin` role.
- Billing API endpoints are rate-limited: 10 requests/minute per user for mutation endpoints (checkout, cancel, upgrade), 60 requests/minute for read endpoints.
- All billing-related actions are logged in an audit trail with: user_id, action, timestamp, IP address, result.

### 7.5 Sensitive Data Handling

- Stripe API keys are never logged, even at DEBUG level.
- Webhook payloads containing customer data are logged with PII redaction (email, name, address redacted; event type and subscription ID retained).
- Database access to billing tables is restricted to the billing service and admin roles.
- Billing data is excluded from general database exports and backups shared with non-admin personnel.

---

## 8. Phase Mapping

### Phase 1: Personal Trading System (Weeks 1-8)

**Billing status: Not required.**

- Single-user system with no authentication or billing.
- All features are unlocked (equivalent to Team tier).
- No Stripe integration.
- No feature gating.
- Database schema does not include billing tables.

**What to build now for later:**
- Design the feature access layer as an abstraction (e.g., `can_access(feature)` function) that returns `True` for all features. This will be replaced by the tier-checking system in Phase 3.
- Use dependency injection for feature checks so the billing integration is a drop-in replacement.

### Phase 2: Analytics & Journaling (Weeks 9-14)

**Billing status: Not required.**

- Continues as single-user system.
- All features remain unlocked.
- Begin documenting which features map to which tiers (preparation for Phase 3).
- Finalize the feature flag registry (BL-FR-013) as a configuration document.

**What to build now for later:**
- Implement usage tracking counters (BL-FR-015) — even without enforcement, start recording journal entry counts, instrument counts, AI usage. This data informs pricing decisions and validates tier limits.
- Ensure all AI feature calls include token counting and cost estimation.

### Phase 3: Multi-Tenant SaaS Launch (Weeks 15-22)

**Billing status: Full implementation.**

| Week | Deliverables |
|---|---|
| 15 | Stripe product/price setup (BL-FR-001). Subscriptions table and data model (BL-FR-027). Stripe customer creation on user registration. |
| 15-16 | Checkout flow (BL-FR-002). Webhook receiver with signature verification and idempotency (BL-FR-016, BL-FR-017, BL-FR-018). Free tier enforcement (BL-FR-005). |
| 16-17 | Feature gating engine: middleware, feature flag registry, tier checking (BL-FR-012, BL-FR-013, BL-FR-014). Redis caching for tier data. |
| 17-18 | Upgrade and downgrade flows (BL-FR-006, BL-FR-007). Proration handling (BL-FR-011). Customer Portal integration (BL-FR-003). |
| 18-19 | Cancellation flow with retention offers (BL-FR-008). Dunning management (BL-FR-020). Failed payment handling (BL-FR-019). |
| 19-20 | Trial period support (BL-FR-023). Coupon/promotion codes (BL-FR-024). Invoice management (BL-FR-021). |
| 20-21 | Revenue analytics dashboard (BL-FR-025). AI usage metering (BL-FR-022). Refund processing (BL-FR-026). |
| 21-22 | End-to-end testing (all BL-TEST-xxx). Reconciliation jobs (BL-NFR-003). Load testing (BL-TEST-008). Bug fixes and polish. |

### Phase 4: Growth & Advanced Features (Months 6-12)

**Billing enhancements (future considerations):**
- Strategy marketplace revenue sharing (creator payouts via Stripe Connect).
- Team plan seat-based pricing (per-seat billing for organizations).
- Volume discounts for prop firm traders with 10+ accounts.
- Multi-currency pricing (EUR, GBP) based on user geography.
- Annual plan gift subscriptions.
- Affiliate/referral program with tracked commissions.
- Custom enterprise tier with negotiated pricing.

---

## 9. Acceptance Criteria

### 9.1 Checkout and Subscription Creation

| ID | Criteria |
|---|---|
| AC-001 | Given a Free tier user on the pricing page, when they select the Pro Monthly plan and complete Stripe Checkout with a valid card, then their tier is updated to `pro` within 10 seconds, they are redirected to the success page, and a welcome email is sent. |
| AC-002 | Given a Free tier user, when they select a plan and Stripe Checkout fails (declined card), then they are returned to the pricing page with the message "Your payment could not be processed. Please try a different payment method." and their tier remains `free`. |
| AC-003 | Given a user who already has an active paid subscription, when they attempt to create a new checkout session, then the system returns `409 Conflict` and directs them to the billing portal. |

### 9.2 Upgrades and Downgrades

| ID | Criteria |
|---|---|
| AC-004 | Given a Trader Monthly subscriber on day 15 of a 30-day cycle, when they upgrade to Pro Monthly, then they are charged approximately $25.00 (prorated difference), their tier updates to `pro` immediately, and they gain access to AI trade reviews within 10 seconds. |
| AC-005 | Given a Pro subscriber, when they downgrade to Trader, then they see the message "Your plan will change to Trader on [end-of-period date]. You have full access until then." and their tier does NOT change until the period ends. |
| AC-006 | Given a Pro subscriber with a pending downgrade, when they click "Cancel Downgrade", then the pending downgrade is removed and they remain on Pro with no changes to their billing. |

### 9.3 Feature Gating

| ID | Criteria |
|---|---|
| AC-007 | Given a Free tier user who has logged 10 journal entries this month, when they complete an 11th trade, then the trade executes (paper mode), the journal entry is created but marked as "over limit", and the user sees "You've reached 10 journal entries this month. Upgrade to Trader for unlimited journaling." |
| AC-008 | Given a Trader tier user, when they attempt to access AI Trade Review, then they see the feature with a lock icon and the message "AI Trade Review is available on Pro and above. Upgrade to unlock AI-powered insights." with a link to the pricing page. |
| AC-009 | Given a user who upgrades from Trader to Pro, when the webhook is processed, then the Redis cache is invalidated and subsequent feature gate checks (within 5 seconds) reflect Pro tier access. |
| AC-010 | Given a Trader user monitoring 10 instruments, when they try to add an 11th, then they see "You're monitoring 10 of 10 instruments. Upgrade to Pro for unlimited." and the 11th instrument is not added. Existing 10 instruments continue monitoring without interruption. |

### 9.4 Payment Failures and Dunning

| ID | Criteria |
|---|---|
| AC-011 | Given a subscriber whose payment fails, when 7 days pass without successful payment, then their access is restricted to Free tier limits, they receive dunning email #4, and a banner displays "Your payment is past due. Update your payment method to restore full access." |
| AC-012 | Given a subscriber in dunning (day 5), when they update their payment method and the retry charge succeeds, then their full tier access is restored within 10 seconds, the dunning state is reset, and they receive a "Payment successful" email. |
| AC-013 | Given a subscriber whose payment has failed all Stripe retry attempts, when Stripe cancels the subscription, then their tier reverts to `free`, they receive a cancellation email, and their data is preserved for 90 days. |

### 9.5 Trials

| ID | Criteria |
|---|---|
| AC-014 | Given a new user who has never had a trial, when they start a 14-day Pro trial, then they gain immediate Pro tier access, their `has_used_trial` flag is set to `true`, and they receive a trial welcome email. |
| AC-015 | Given a trial user on day 14, when the trial ends and their payment method is valid, then they are automatically charged $99.00 and their status changes from `trialing` to `active`. |
| AC-016 | Given a trial user who cancels on day 10, then they retain Pro access until day 14, no charge is made, and they revert to Free tier on day 14. |
| AC-017 | Given a user who has previously used a trial, when they attempt to start another trial, then they are shown "You've already used your free trial. Subscribe to Pro for $99/month." and no trial is created. |

### 9.6 Webhooks and Data Integrity

| ID | Criteria |
|---|---|
| AC-018 | Given a valid Stripe webhook event, when it is delivered to the webhook endpoint, then the endpoint responds with `200 OK` within 5 seconds and the event is queued for processing. |
| AC-019 | Given a webhook request with an invalid signature, when it hits the webhook endpoint, then it is rejected with `400 Bad Request` and no processing occurs. |
| AC-020 | Given the same webhook event delivered twice (duplicate), when the second delivery arrives, then it returns `200 OK` without processing the event again (no duplicate emails, no duplicate tier changes). |
| AC-021 | Given the daily reconciliation job runs, when a discrepancy is found between local and Stripe subscription state, then a `CRITICAL` alert is fired, the local state is corrected to match Stripe, and the discrepancy is logged with full details. |

### 9.7 Admin Operations

| ID | Criteria |
|---|---|
| AC-022 | Given an admin on the revenue dashboard, when the page loads, then they see current MRR, active subscriber count by tier, monthly churn rate, and a 12-month MRR trend chart, all reflecting data no more than 15 minutes old. |
| AC-023 | Given an admin processing a refund, when they select an invoice, enter a reason, and submit a full refund, then Stripe processes the refund, the invoice status updates to `refunded`, the user receives a refund notification email, and the refund is logged in the `refunds` table. |
| AC-024 | Given a non-admin user, when they attempt to access `/admin/revenue` or any admin billing endpoint, then they receive `403 Forbidden`. |

### 9.8 Performance

| ID | Criteria |
|---|---|
| AC-025 | Given 1,000 concurrent authenticated users, when feature gate checks are performed, then p99 latency is under 50ms. |
| AC-026 | Given a burst of 100 webhook events delivered in 1 second, then all events are acknowledged with `200 OK` within 5 seconds each and all are fully processed within 30 seconds. |

---

## Appendix

### A. Stripe API Endpoints Used

| Stripe Resource | Operations | TrendEdge Usage |
|---|---|---|
| Products | Create, Retrieve | Tier product definitions |
| Prices | Create, Retrieve, List | Monthly and annual price configurations |
| Customers | Create, Retrieve, Update | One-to-one mapping with TrendEdge users |
| Subscriptions | Create, Retrieve, Update, Cancel | Subscription lifecycle management |
| Checkout Sessions | Create | New subscription checkout |
| Billing Portal Sessions | Create | Self-service billing management |
| Invoices | Retrieve, List | Invoice history and PDF access |
| Refunds | Create | Admin-initiated refunds |
| Coupons | Create, Retrieve, Update, Delete | Discount management |
| Promotion Codes | Create, Retrieve, Update | User-facing discount codes |
| Webhooks | Receive | Event-driven subscription management |
| Payment Methods | Retrieve | Display card info (last 4, brand) |

### B. Email Templates Required

| Template | Trigger | Key Content |
|---|---|---|
| `welcome_paid` | Subscription created | Tier features, getting started guide |
| `welcome_trial` | Trial started | Trial features, trial end date, how to cancel |
| `trial_midpoint` | Day 7 of trial | Usage summary, trial value highlights |
| `trial_ending` | 3 days before trial end | End date, charge amount, cancel instructions |
| `trial_converted` | Trial auto-converts | Confirmation, next billing date |
| `trial_expired` | Trial cancelled/expired | What was lost, upgrade CTA |
| `upgrade_confirmation` | Upgrade processed | New features, prorated charge amount |
| `downgrade_scheduled` | Downgrade requested | Effective date, what changes, cancel downgrade CTA |
| `downgrade_effective` | Downgrade takes effect | New tier, feature changes, upgrade CTA |
| `cancellation_confirmation` | Cancellation requested | Access end date, data retention, reactivate CTA |
| `cancellation_effective` | Subscription cancelled | Reactivation instructions, data retention timeline |
| `payment_failed_1` | First payment failure | Update payment method CTA |
| `payment_failed_2` | Second failure | Urgency, access restriction warning |
| `payment_grace_ending` | 6 days after first failure | Final warning before restriction |
| `access_restricted` | 7 days after first failure | Restricted features, restore access CTA |
| `payment_final_warning` | 3 days before cancellation | Cancellation imminent, urgent CTA |
| `payment_recovered` | Successful retry after failure | Access restored confirmation |
| `invoice_receipt` | Payment succeeded | Amount, invoice link, next billing date |
| `refund_issued` | Refund processed | Refund amount, expected timeline |
| `reactivation_confirmation` | Subscription reactivated | Restored features, next billing date |
| `pause_confirmation` | Subscription paused | Resume date, Free tier access during pause |
| `pause_resuming` | 3 days before auto-resume | Resume date, billing restart |

### C. Glossary

| Term | Definition |
|---|---|
| MRR | Monthly Recurring Revenue. Sum of all active subscription monthly-equivalent fees. Annual subscriptions divided by 12. |
| ARR | Annual Recurring Revenue. MRR multiplied by 12. |
| Churn Rate | Percentage of subscribers who cancel in a given month, relative to total subscribers at the start of that month. |
| Dunning | The process of communicating with customers about failed payments to recover revenue. |
| Proration | Adjusting a charge to account for a partial billing period when a plan changes mid-cycle. |
| Feature Gate | A programmatic check that determines whether a user has access to a specific feature based on their subscription tier. |
| Grace Period | The time between a payment failure and access restriction, during which the user retains full access. |
| SAQ-A | PCI Self-Assessment Questionnaire A, the simplest PCI compliance level for merchants who fully outsource payment processing. |
| LTV | Lifetime Value. Total revenue expected from a customer over their entire relationship. |
| CAC | Customer Acquisition Cost. Total marketing and sales spend divided by new customers acquired. |
| ARPU | Average Revenue Per User. Total revenue divided by total active subscribers. |
