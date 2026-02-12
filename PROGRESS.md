# TrendEdge — Project Progress Tracker

**Last Updated:** 2026-02-12
**Overall Status:** Early Development (~30% complete)

---

## Agent Quick Reference — FSD Implementation Status

> **Agents: scan this table FIRST.** Update status and dates here when starting or completing work.
> Statuses: `not started` | `in-progress` | `done`

| FSD | Domain | Status | Started | Completed |
|-----|--------|--------|---------|-----------|
| FSD-001 | Platform Infrastructure | done | — | 2026-02-12 |
| FSD-002 | Trendline Detection | done | 2026-02-12 | 2026-02-12 |
| FSD-003 | Trade Execution (main) | not started | — | — |
| FSD-003a | Signal Ingestion | not started | — | — |
| FSD-003b | Risk Management | not started | — | — |
| FSD-003c | Broker Adapters | not started | — | — |
| FSD-003d | Order Lifecycle | not started | — | — |
| FSD-004 | Trade Journaling | not started | — | — |
| FSD-005 | Playbook System | not started | — | — |
| FSD-006 | Performance Analytics (main) | not started | — | — |
| FSD-006a | Metrics Engine | not started | — | — |
| FSD-006b | Visualization Dashboard | not started | — | — |
| FSD-006c | Advanced Analytics | not started | — | — |
| FSD-007 | AI Features | not started | — | — |
| FSD-008 | Auth & User Mgmt (main) | done | 2026-02-12 | 2026-02-12 |
| FSD-008a | Authentication | done | 2026-02-12 | 2026-02-12 |
| FSD-008b | User Profiles | done | 2026-02-12 | 2026-02-12 |
| FSD-008c | Broker Connections | done | 2026-02-12 | 2026-02-12 |
| FSD-008d | Authorization & Multitenancy | done | 2026-02-12 | 2026-02-12 |
| FSD-009 | Billing & Subscriptions (main) | not started | — | — |
| FSD-009a | Stripe Subscriptions | not started | — | — |
| FSD-009b | Feature Gating | not started | — | — |
| FSD-009c | Billing Admin | not started | — | — |
| FSD-010 | Notifications (main) | not started | — | — |
| FSD-010a | Notification Engine | not started | — | — |
| FSD-010b | Channel Integrations | not started | — | — |
| FSD-010c | Market Data | not started | — | — |
| FSD-011 | Frontend Dashboard (main) | in-progress | — | — |
| FSD-011a | App Shell | in-progress | 2026-02-12 | — |
| FSD-011b | Dashboard & Trendlines | in-progress | 2026-02-12 | — |
| FSD-011c | Execution & Journal Views | not started | — | — |
| FSD-011d | Analytics & Playbook Views | not started | — | — |
| FSD-011e | Settings, Onboarding & Chat | not started | — | — |

---

## Executive Summary

TrendEdge is an AI-powered futures trading platform with 11 product domains defined across PRDs and FSDs. The project currently has **foundational infrastructure and authentication implemented** on both backend and frontend. The core trading features (trendline detection, execution, journaling, analytics) are fully specified but not yet built.

---

## Phase Overview

| Phase | Timeline | Focus | Status |
|-------|----------|-------|--------|
| **Phase 1** | Weeks 1-8 | Infrastructure, trendlines, execution, paper trading, basic journal | In Progress |
| **Phase 2** | Weeks 9-14 | Multi-broker, playbooks, advanced analytics, AI features, notifications | Not Started |
| **Phase 3** | Weeks 15-22 | Billing, teams, onboarding, Discord, admin dashboard | Not Started |
| **Phase 4** | Future | Growth features, mobile app, marketplace | Not Started |

---

## Feature Domain Progress

### PRD-001: Platform Infrastructure & DevOps
**Status: 95% Complete** | Phase 1 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI application factory | Done | Lifespan management, env validation, exception handlers |
| Middleware stack | Done | RequestID, Timing, CORS, RateLimit, RequestLogging |
| Structured logging (structlog) | Done | JSON-only, no secret leaking |
| Exception handling system | Done | 7 custom exceptions, global handlers, Sentry integration |
| PostgreSQL (Supabase) connection | Done | Async SQLAlchemy 2.0, connection pooling |
| Redis (Upstash) client | Done | TLS, singleton pattern, graceful degradation |
| Redis caching helpers | Done | Pattern-based cache with JSON serialization |
| Rate limiting (sliding window) | Done | Redis sorted sets, per-user/per-IP, fails open |
| Celery task queue setup | Done | 4 queues (high/default/low/notifications), routing rules |
| Docker Compose (5 services) | Done | PostgreSQL 16, Redis 7, API, Worker, Beat |
| Dockerfile (multi-stage) | Done | Python 3.12-slim, production-ready |
| Makefile | Done | dev, test, lint, migrate, seed commands |
| Health endpoints | Done | /health, /health/ready, /health/detailed |
| CI/CD pipeline (GitHub Actions) | Done | CI (lint, unit, integration, build) + CD (Railway placeholder) |
| Monitoring (Sentry/Axiom/Uptime Robot) | Partial | Sentry configured, Axiom/Uptime Robot are external service configs |
| Seed data script | Done | 4 users (admin/free/trader/pro) + audit logs, idempotent |
| Backend test suite | Done | 4 unit test files (14 tests) + 2 integration test files |

**Spec Coverage:** FSD-001 fully written

---

### PRD-002: Trendline Detection Engine
**Status: 98% Complete** | Phase 1 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Market data ingestion (yfinance) | Done | MarketDataService with bootstrap + incremental ingest |
| Candle storage & gap detection | Done | Bulk upsert with ON CONFLICT, gap_detection_and_fill task |
| ATR computation (14-period) | Done | Wilder's smoothed ATR in MarketDataService |
| Swing point detection (pivot highs/lows) | Done | scipy.signal.find_peaks, boundary exclusion, flat handling |
| Candidate trendline generation | Done | Pairwise generation with body-cross validation, slope normalization |
| Touch scoring & validation | Done | ATR-scaled tolerance, spacing enforcement, composite score |
| Quality grading (A+/A/B) & composite score | Done | Full rubric with user config overrides |
| Trendline state machine | Done | detected -> qualifying -> active -> traded/invalidated/expired |
| State machine transitions (promote/demote/expire) | Done | promote_or_demote_trendlines (3*ATR threshold), expire_stale_trendlines (6mo) |
| Proximity-based score decay | Done | Score decay when distance > 5*ATR, factor = 5*ATR/distance |
| Alert generation & routing | Done | Break/touch/promotion/invalidation alerts with dedup |
| DB tables (8 total) | Done | instruments, candles, pivots, trendlines, trendline_events, alerts, user_detection_config, user_watchlist |
| API endpoints (route-service alignment) | Done | trendlines, instruments, watchlist, detection_config, alerts; Pydantic response models aligned |
| Celery tasks (6 tasks) | Done | ingest, detect, evaluate_alerts, recalculate, bootstrap, gap_fill |
| Celery Beat schedule | Done | ingest_candles every 4H, gap_detection_and_fill daily 6AM UTC |
| Unit tests (detection engine) | Done | 33+ tests: pivots, candidates, scoring, grading, projection, ATR |
| Integration tests (pipeline) | Done | 16 tests: bootstrap, config, tier limits, alerts, lifecycle, decay, watchlist |
| Forward projection & bracket orders | Done | Safety line, entry/stop/target, position sizing |
| IBKR live data integration | Not Started | Phase 2: broker adapter data feed |

**Spec Coverage:** FSD-002 fully written

---

### PRD-003: Trade Execution Pipeline
**Status: 0% Complete** | Phase 1 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Signal ingestion (internal, TradingView, manual) | Not Started | FSD-003a |
| Signal normalization & deduplication | Not Started | FSD-003a |
| Risk management engine | Not Started | FSD-003b |
| Broker adapter ABC | Not Started | FSD-003c |
| IBKR adapter (ib_async) | Not Started | FSD-003c |
| Tradovate adapter (REST/WebSocket) | Not Started | FSD-003c |
| Webull adapter (SDK) | Not Started | FSD-003c, Phase 2 |
| Paper trading simulator | Not Started | FSD-003c |
| Order lifecycle management | Not Started | FSD-003d |
| Bracket order construction | Not Started | FSD-003d |
| Position tracking & fill management | Not Started | FSD-003d |
| Circuit breaker (3 failures, 15-min cooldown) | Not Started | |
| DB tables: signals, orders, positions, fills | Not Started | |

**Spec Coverage:** FSD-003, FSD-003a, FSD-003b, FSD-003c, FSD-003d fully written

---

### PRD-004: Trade Journaling
**Status: 0% Complete** | Phase 1-2 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Auto-journal creation on trade.fill | Not Started | |
| Auto-population (20+ fields) | Not Started | |
| MAE/MFE tick-by-tick tracking | Not Started | |
| Manual enrichment (conviction, tags, notes) | Not Started | |
| Screenshot upload (Cloudflare R2) | Not Started | |
| Trade search & filtering | Not Started | |
| Trade linking (scale-in/out) | Not Started | |
| CSV/PDF export | Not Started | |
| DB tables: journal_entries, screenshots | Not Started | |

**Spec Coverage:** FSD-004 fully written

---

### PRD-005: Playbook System
**Status: 0% Complete** | Phase 1-2 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Default playbooks (A+ Break, Standard, Bounce) | Not Started | |
| Custom playbook CRUD | Not Started | |
| Auto-classification rules engine | Not Started | |
| Per-playbook metrics | Not Started | |
| Playbook comparison views | Not Started | |
| Rule compliance tracking | Not Started | |
| DB tables: playbooks, rules, assignments | Not Started | |

**Spec Coverage:** FSD-005 fully written

---

### PRD-006: Performance Analytics
**Status: 0% Complete** | Phase 2 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Metrics engine (30+ metrics, 7 categories) | Not Started | FSD-006a |
| Materialized views for aggregation | Not Started | FSD-006a |
| Visualization dashboard | Not Started | FSD-006b |
| Advanced analytics (Monte Carlo, correlation) | Not Started | FSD-006c, Pro tier |
| Redis cache (5-min TTL) | Not Started | |
| WebSocket real-time updates | Not Started | |
| API endpoints: /api/v1/analytics/* | Not Started | |

**Spec Coverage:** FSD-006, FSD-006a, FSD-006b, FSD-006c fully written

---

### PRD-007: AI Features
**Status: 0% Complete** | Phase 2 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Trendline quality scoring (GBClassifier) | Not Started | |
| False breakout filter (XGBoost/LightGBM) | Not Started | |
| Conversational analytics (Claude API) | Not Started | |
| Trade review assistant | Not Started | |
| AI insights dashboard widget | Not Started | |
| Cost tracking & usage metering | Not Started | |
| DB tables: ml_features, model_artifacts | Not Started | |

**Spec Coverage:** FSD-007 fully written

---

### PRD-008: Authentication & User Management
**Status: 85% Complete** | Phase 1-2 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Supabase Auth integration | Done | JWT validation, signup/login/logout/refresh |
| Email/password registration | Done | Password complexity validation (8+ chars, upper/lower/digit/special) |
| Login with account lockout | Done | 10+ failures -> 15-min lock, 50+ -> 1-hour lock |
| Token refresh | Done | Via Supabase REST API |
| Audit logging | Done | user_registered, login_success, login_failure events + all new auth events |
| User model + RLS policies | Done | SELECT/UPDATE own row only, display_name/timezone/avatar_url columns |
| Magic link authentication | Done | FSD-008a: POST /auth/magic-link, /auth/verify-otp |
| OAuth (Google, GitHub) | Done | FSD-008a: GET /auth/oauth/{provider}, callback handling |
| Email verification flow | Done | FSD-008a: POST /auth/verify/resend |
| Password reset flow | Done | FSD-008a: POST /auth/password/reset, /password/update, /password/change |
| Profile management (display_name, timezone) | Done | FSD-008b: GET/PATCH /profile |
| Trading preferences | Done | FSD-008b: PATCH /profile/trading with deep merge |
| Notification preferences | Done | FSD-008b: PATCH /profile/notifications (Telegram/Discord/email) |
| Display preferences | Done | FSD-008b: PATCH /profile/display (theme/currency/date format) |
| Broker connection management | Done | FSD-008c: full CRUD + test endpoints, tier enforcement |
| AES-256-GCM credential encryption | Done | FSD-008c: HKDF-SHA256 per-connection key derivation |
| Broker connections RLS | Done | FSD-008c: SELECT/INSERT/UPDATE/DELETE policies |
| RBAC (user, admin roles) | Done | FSD-008d: DB-based role verification, Redis permission cache (5min TTL) |
| Permission system + tier limits | Done | FSD-008d: require_role, require_verified_email, check_tier_limit |
| API key management | Done | FSD-008d: CRUD, SHA-256 hash storage, te_live_/te_test_ prefixes |
| API key authentication middleware | Done | FSD-008d: X-API-Key header, rate limiting 60/min per key |
| API keys RLS | Done | FSD-008d: SELECT/INSERT/UPDATE/DELETE policies |
| Session management (multi-device) | Not Started | FSD-008a, Phase 2 |
| Avatar upload (Cloudflare R2) | Not Started | FSD-008b, Phase 2 |
| Team/organization support | Not Started | FSD-008d, Phase 3 |
| Onboarding wizard | Not Started | FSD-008b, Phase 3 |
| Account deletion (30-day grace) | Not Started | FSD-008d, Phase 3 |
| Data export (ZIP) | Not Started | FSD-008d, Phase 3 |

**Spec Coverage:** FSD-008, FSD-008a, FSD-008b, FSD-008c, FSD-008d fully written

---

### PRD-009: Billing & Subscriptions
**Status: 0% Complete** | Phase 3 | Priority: P1

| Component | Status | Notes |
|-----------|--------|-------|
| Stripe products/prices configuration | Not Started | FSD-009a |
| Checkout session creation | Not Started | FSD-009a |
| Customer Portal integration | Not Started | FSD-009a |
| Subscription lifecycle (upgrade/downgrade) | Not Started | FSD-009a |
| Feature gating middleware | Not Started | FSD-009b |
| Usage tracking | Not Started | FSD-009b |
| Dunning management (6-step sequence) | Not Started | FSD-009c |
| Revenue analytics (MRR, churn, LTV) | Not Started | FSD-009c |
| Webhook handler (idempotent) | Not Started | FSD-009a |
| DB tables: subscriptions, stripe_events | Not Started | |

**Spec Coverage:** FSD-009, FSD-009a, FSD-009b, FSD-009c fully written

---

### PRD-010: Notifications & Integrations
**Status: 0% Complete** | Phase 1-2 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Notification engine (Redis pub/sub) | Not Started | FSD-010a |
| Template rendering (per event/channel) | Not Started | FSD-010a |
| Delivery tracking & retry logic | Not Started | FSD-010a |
| Circuit breaker per channel | Not Started | FSD-010a |
| Telegram bot integration | Not Started | FSD-010b |
| Discord webhook integration | Not Started | FSD-010b |
| Email (SendGrid/Resend) | Not Started | FSD-010b |
| In-app notification center | Not Started | FSD-010b |
| TradingView webhook receiver | Not Started | FSD-010b |
| Market data integration (yfinance, IBKR) | Not Started | FSD-010c |
| Quiet hours / DND | Not Started | FSD-010a |
| DB tables: notification_log, preferences | Not Started | |

**Spec Coverage:** FSD-010, FSD-010a, FSD-010b, FSD-010c fully written

---

### PRD-011: Frontend Dashboard & UI/UX
**Status: 35% Complete** | Phase 1-3 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Next.js 14 App Router setup | Done | TypeScript, Tailwind, shadcn/ui |
| Supabase client (browser + server) | Done | SSR-compatible createClient helpers |
| Auth middleware (session refresh) | Done | Supabase middleware for cookie-based auth |
| BFF proxy route (/api/[...proxy]) | Done | Proxies all API calls to FastAPI backend |
| Login page | Done | Email/password form |
| Registration page | Done | Email/password with validation |
| Auth callback handler | Done | OAuth redirect handler |
| Auth layout (centered card) | Done | Shared layout for login/register |
| Base UI components (Button, Input, Card, Label) | Done | shadcn/ui primitives |
| Extended UI components | Done | Tabs, Select, Dialog, Tooltip, Badge, Slider, Accordion, Sheet, Skeleton, etc. |
| CSS design tokens (light/dark) | Done | HSL variables incl. trading colors (profit/loss/grades/alerts) |
| Providers (QueryClient + Toaster) | Done | TanStack Query + sonner |
| TypeScript types | Done | Trendline, Dashboard, API types matching backend schemas |
| API client | Done | Typed fetch wrapper using BFF proxy |
| Zustand stores | Done | UI store, trendline store, positions store |
| TanStack Query hooks | Done | Dashboard queries, trendline queries, instrument queries |
| Mock data system | Done | Gated by NEXT_PUBLIC_USE_MOCKS env var |
| Format utilities | Done | formatDollars, formatPercent, formatR, formatRelativeTime |
| Sidebar navigation | Done | FSD-011a: collapsible with lucide icons |
| Header bar (mode indicator) | Done | FSD-011a: Paper/Live badge, avatar placeholder |
| Dashboard layout (3-col) | Done | FSD-011a: sidebar + header + main content area |
| Command palette (Cmd+K) | Not Started | FSD-011a |
| Dashboard home page | Done | FSD-011b: P&L, stats, positions, alerts, recent trades widgets |
| Trendline detection page | Done | FSD-011b: 3-column with chart, list panel, detail/config panel |
| Candlestick chart | Done | FSD-011b: TradingView Lightweight Charts with trendline overlays |
| Detection config panel | Done | FSD-011b: 6 params with sliders, presets, apply/reset |
| Execution page | Not Started | FSD-011c |
| Journal page | Not Started | FSD-011c |
| Analytics dashboard | Not Started | FSD-011d |
| Playbook management pages | Not Started | FSD-011d |
| Settings pages | Not Started | FSD-011e |
| Onboarding wizard | Not Started | FSD-011e, Phase 3 |
| AI chat interface | Not Started | FSD-011e |

**Spec Coverage:** FSD-011, FSD-011a, FSD-011b, FSD-011c, FSD-011d, FSD-011e fully written

---

## Database Schema Progress

| Table | Migration | Model | Repository | RLS |
|-------|-----------|-------|------------|-----|
| users | Done | Done | Not Started | Done |
| audit_logs | Done | Done | Not Started | Done |
| broker_connections | Done | Done | Not Started | Done |
| api_keys | Done | Done | Not Started | Done |
| instruments | Done | Done | Not Started | No (shared ref) |
| candles | Done | Done | Not Started | No (shared data) |
| pivots | Done | Done | Not Started | No |
| trendlines | Done | Done | Not Started | Done |
| trendline_events | Done | Done | Not Started | No |
| alerts | Done | Done | Not Started | Done |
| user_detection_config | Done | Done | Not Started | Done |
| user_watchlist | Done | Done | Not Started | Done |
| signals | Not Started | Not Started | Not Started | -- |
| orders | Not Started | Not Started | Not Started | -- |
| positions | Not Started | Not Started | Not Started | -- |
| fills | Not Started | Not Started | Not Started | -- |
| journal_entries | Not Started | Not Started | Not Started | -- |
| journal_screenshots | Not Started | Not Started | Not Started | -- |
| playbooks | Not Started | Not Started | Not Started | -- |
| subscriptions | Not Started | Not Started | Not Started | -- |
| notification_log | Not Started | Not Started | Not Started | -- |
| ml_trendline_features | Not Started | Not Started | Not Started | -- |

---

## API Endpoint Progress

| Endpoint Group | Specified | Implemented | Coverage |
|---------------|-----------|-------------|----------|
| Health (/health/*) | 3 | 3 | 100% |
| Auth (/auth/*) | 11 | 11 | 100% |
| Profile (/profile/*) | 5 | 5 | 100% |
| Broker Connections (/broker-connections/*) | 6 | 6 | 100% |
| API Keys (/api-keys/*) | 4 | 4 | 100% |
| Trendlines (/trendlines/*) | ~8 | 3 | ~38% |
| Instruments (/instruments/*) | ~4 | 2 | 50% |
| Watchlist (/watchlist/*) | 3 | 3 | 100% |
| Detection Config (/config/*) | 3 | 3 | 100% |
| Alerts (/alerts/*) | 3 | 3 | 100% |
| Signals (/signals/*) | ~5 | 0 | 0% |
| Orders (/orders/*) | ~6 | 0 | 0% |
| Journal (/journal/*) | ~8 | 0 | 0% |
| Playbooks (/playbooks/*) | ~7 | 0 | 0% |
| Analytics (/analytics/*) | ~6 | 0 | 0% |
| AI (/chat/*) | ~4 | 0 | 0% |
| Billing (/billing/*) | ~6 | 0 | 0% |
| Notifications (/notifications/*) | ~5 | 0 | 0% |
| Webhooks (/webhooks/*) | ~3 | 0 | 0% |
| **Total** | **~81** | **47** | **~58%** |

---

## Testing Progress

| Category | Written | Status |
|----------|---------|--------|
| Backend unit tests | 47+ | 5 files: test_health, test_error_handling, test_middleware, test_config, test_detection_engine |
| Backend integration tests | 18 | 3 files: test_db_health, test_redis_health, test_trendline_pipeline (16 tests) |
| Backend e2e tests | 0 | Not started |
| Frontend unit tests (Jest) | 0 | Not started |
| Frontend e2e tests (Playwright) | 0 | Not started |
| Accessibility (axe-core) | 0 | Not started |

---

## Documentation Progress

| Document | Status |
|----------|--------|
| PRD-001 through PRD-011 | All written |
| FSD-001 through FSD-011e (34 total) | All written |
| CLAUDE.md (project conventions) | Written |
| Technical Spec Writing Guide | Written |
| API documentation | Not started |
| Deployment guide | Not started |

---

## What's Built (Production-Ready)

1. FastAPI application with lifespan, middleware, and error handling
2. PostgreSQL async ORM (4 models: User, AuditLog, BrokerConnection, ApiKey) with RLS
3. Redis client + caching + sliding-window rate limiting
4. Supabase authentication (signup, login, logout, refresh, magic link, OAuth, password reset, email verification) with account lockout
5. User profile management (display name, timezone, trading/notification/display preferences)
6. Broker connection management with AES-256-GCM credential encryption and tier enforcement
7. API key management with SHA-256 hash storage and per-key rate limiting
8. Role-based access control with DB-verified roles and Redis permission cache
9. Celery task queue infrastructure (7 queues: high, default, low, notifications, market_data, detection, alerts) with Beat schedule
10. Docker Compose local dev stack (5 services, health checks)
11. Next.js frontend with Supabase auth, BFF proxy, login/register pages
12. Trendline detection engine: pivot detection (scipy), candidate generation, touch scoring, grading (A+/A/B), composite ranking
13. Market data service: yfinance ingestion, ATR computation, gap detection
14. Trendline service: full detection pipeline, state machine (with promote/demote/expire), alert evaluation, watchlist management, proximity-based score decay
15. 8 PRD-002 DB tables with RLS policies (instruments, candles, pivots, trendlines, trendline_events, alerts, user_detection_config, user_watchlist)
16. 14 new API endpoints: trendlines, instruments, watchlist, detection config, alerts (all with proper Pydantic response alignment)
17. 6 Celery tasks with Beat schedule: candle ingestion (4H), incremental detection, alert evaluation, full recalculation, bootstrap, gap detection (daily 6AM)
18. 16 trendline pipeline integration tests: bootstrap, config, tier limits, alert dedup, lifecycle, state transitions, proximity decay, watchlist
19. Frontend app shell: sidebar navigation, header bar, dashboard layout, providers, Zustand stores, TanStack Query hooks
20. Dashboard home page: P&L summary, quick stats, active positions, trendline alerts, recent trades widgets
21. Trendline detection page: candlestick chart (Lightweight Charts), trendline list panel, detail panel, detection config panel with presets

## Recommended Build Order

> **Strategy: Vertical slices, phase-ordered.** Each phase builds backend AND its matching frontend pages in parallel. There is no separate frontend phase — FSD-011 sub-specs are distributed across phases.

| # | Backend PRD | Domain | Backend FSDs | Frontend (parallel) | Depends On |
|---|-------------|--------|-------------|---------------------|------------|
| 1 | PRD-001 | Platform Infrastructure | FSD-001 | — | — |
| 2 | PRD-008 | Auth & User Management | FSD-008, 008a-008d | **FSD-011a** (app shell, nav, layout) | — |
| | | **— Phase 1 complete —** | | | |
| 3 | PRD-002 | Trendline Detection | FSD-002 | **FSD-011b** (dashboard home, trendline views) | Phase 1 |
| 4 | PRD-003 | Trade Execution | FSD-003, 003a-003d | *(covered by 011b + 011c)* | Phase 1 |
| | | **— Phase 2 complete —** | | | |
| 5 | PRD-004 | Trade Journaling | FSD-004 | **FSD-011c** (execution & journal views) | Phase 2 |
| 6 | PRD-005 | Playbook System | FSD-005 | *(covered by 011d)* | Phase 2 |
| | | **— Phase 3 complete —** | | | |
| 7 | PRD-010 | Notifications & Integrations | FSD-010, 010a-010c | — | Phase 1 |
| 8 | PRD-006 | Performance Analytics | FSD-006, 006a-006c | **FSD-011d** (analytics & playbook views) | Phase 3 |
| 9 | PRD-007 | AI Features | FSD-007 | *(covered by 011e)* | Phase 3 |
| | | **— Phase 4 complete —** | | | |
| 10 | PRD-009 | Billing & Subscriptions | FSD-009, 009a-009c | **FSD-011e** (settings, onboarding, AI chat) | Phase 1 |
| | | **— Phase 5 complete —** | | | |

### Why this order?

- **PRD-001 + PRD-008 first**: Everything else depends on infra and auth being solid.
- **FSD-011a with Phase 1**: App shell, sidebar, nav, and theme system are needed before any feature pages.
- **PRD-002 before PRD-003**: Trendline detection feeds signals into trade execution.
- **FSD-011b with Phase 2**: Dashboard home and trendline views consume the APIs built in this phase.
- **PRD-004 + PRD-005 after execution**: Journaling and playbooks consume trade data.
- **FSD-011c with Phase 3**: Execution and journal pages are built alongside their backend APIs.
- **PRD-010 early (after Phase 1)**: Notifications are independent of trading features.
- **PRD-006 + PRD-007 late**: Analytics and AI need trade data to be meaningful.
- **FSD-011d with Phase 4**: Analytics dashboard and playbook views ship with their backend.
- **PRD-009 late**: Billing/gating isn't needed until features exist to gate.
- **FSD-011e with Phase 5**: Settings, onboarding wizard, and AI chat round out the frontend.
