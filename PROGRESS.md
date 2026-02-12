# TrendEdge — Project Progress Tracker

**Last Updated:** 2026-02-12
**Overall Status:** Early Development (~15% complete)

---

## Agent Quick Reference — FSD Implementation Status

> **Agents: scan this table FIRST.** Update status and dates here when starting or completing work.
> Statuses: `not started` | `in-progress` | `done`

| FSD | Domain | Status | Started | Completed |
|-----|--------|--------|---------|-----------|
| FSD-001 | Platform Infrastructure | done | — | 2026-02-12 |
| FSD-002 | Trendline Detection | not started | — | — |
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
| FSD-008 | Auth & User Mgmt (main) | in-progress | — | — |
| FSD-008a | Authentication | in-progress | — | — |
| FSD-008b | User Profiles | not started | — | — |
| FSD-008c | Broker Connections | not started | — | — |
| FSD-008d | Authorization & Multitenancy | not started | — | — |
| FSD-009 | Billing & Subscriptions (main) | not started | — | — |
| FSD-009a | Stripe Subscriptions | not started | — | — |
| FSD-009b | Feature Gating | not started | — | — |
| FSD-009c | Billing Admin | not started | — | — |
| FSD-010 | Notifications (main) | not started | — | — |
| FSD-010a | Notification Engine | not started | — | — |
| FSD-010b | Channel Integrations | not started | — | — |
| FSD-010c | Market Data | not started | — | — |
| FSD-011 | Frontend Dashboard (main) | in-progress | — | — |
| FSD-011a | App Shell | not started | — | — |
| FSD-011b | Dashboard & Trendlines | not started | — | — |
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
**Status: 0% Complete** | Phase 1 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Market data ingestion (yfinance/IBKR) | Not Started | |
| Candle storage & gap detection | Not Started | |
| ATR computation (14-period) | Not Started | |
| Swing point detection (pivot highs/lows) | Not Started | |
| Candidate trendline generation (RANSAC) | Not Started | |
| Touch scoring & validation | Not Started | |
| Quality grading (A+/A/B) & composite score | Not Started | |
| Trendline state machine | Not Started | detected -> qualifying -> active -> traded -> invalidated -> expired |
| Alert generation & routing | Not Started | |
| DB tables: candles, pivots, trendlines, alerts | Not Started | |
| API endpoints: /api/v1/trendlines/* | Not Started | |

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
**Status: 40% Complete** | Phase 1 | Priority: P0

| Component | Status | Notes |
|-----------|--------|-------|
| Supabase Auth integration | Done | JWT validation, signup/login/logout/refresh |
| Email/password registration | Done | Password complexity validation (8+ chars, upper/lower/digit/special) |
| Login with account lockout | Done | 10+ failures -> 15-min lock, 50+ -> 1-hour lock |
| Token refresh | Done | Via Supabase REST API |
| Audit logging | Done | user_registered, login_success, login_failure events |
| User model + RLS policies | Done | SELECT/UPDATE own row only |
| Magic link authentication | Not Started | FSD-008a |
| OAuth (Google, GitHub) | Not Started | FSD-008a |
| Email verification flow | Not Started | FSD-008a |
| Password reset flow | Not Started | FSD-008a |
| Session management (multi-device) | Not Started | FSD-008a |
| Profile management (avatar, timezone) | Not Started | FSD-008b |
| Trading preferences | Not Started | FSD-008b |
| Broker connection management | Not Started | FSD-008c |
| AES-256-GCM credential encryption | Not Started | FSD-008c |
| RBAC (user, admin, team roles) | Not Started | FSD-008d |
| Team/organization support | Not Started | FSD-008d, Phase 3 |
| API key management | Not Started | FSD-008d |
| Account deletion (30-day grace) | Not Started | FSD-008d |

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
**Status: 15% Complete** | Phase 1-3 | Priority: P0

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
| CSS design tokens (light/dark) | Done | HSL variables in globals.css |
| Sidebar navigation | Not Started | FSD-011a |
| Header bar (breadcrumbs, mode indicator) | Not Started | FSD-011a |
| Command palette (Cmd+K) | Not Started | FSD-011a |
| Dashboard home page | Not Started | FSD-011b |
| Trendline detection page | Not Started | FSD-011b |
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
| candles | Not Started | Not Started | Not Started | -- |
| pivots | Not Started | Not Started | Not Started | -- |
| trendlines | Not Started | Not Started | Not Started | -- |
| alerts | Not Started | Not Started | Not Started | -- |
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
| Auth (/auth/*) | 4 | 4 | 100% |
| Trendlines (/trendlines/*) | ~8 | 0 | 0% |
| Instruments (/instruments/*) | ~4 | 0 | 0% |
| Signals (/signals/*) | ~5 | 0 | 0% |
| Orders (/orders/*) | ~6 | 0 | 0% |
| Journal (/journal/*) | ~8 | 0 | 0% |
| Playbooks (/playbooks/*) | ~7 | 0 | 0% |
| Analytics (/analytics/*) | ~6 | 0 | 0% |
| AI (/chat/*) | ~4 | 0 | 0% |
| Billing (/billing/*) | ~6 | 0 | 0% |
| Notifications (/notifications/*) | ~5 | 0 | 0% |
| Webhooks (/webhooks/*) | ~3 | 0 | 0% |
| **Total** | **~69** | **7** | **~10%** |

---

## Testing Progress

| Category | Written | Status |
|----------|---------|--------|
| Backend unit tests | 14 | 4 files: test_health, test_error_handling, test_middleware, test_config |
| Backend integration tests | 2 | 2 files: test_db_health, test_redis_health (requires_db/requires_redis) |
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
2. PostgreSQL async ORM (2 models: User, AuditLog) with RLS
3. Redis client + caching + sliding-window rate limiting
4. Supabase authentication (signup, login, logout, refresh) with account lockout
5. Celery task queue infrastructure (4 priority queues)
6. Docker Compose local dev stack (5 services, health checks)
7. Next.js frontend with Supabase auth, BFF proxy, login/register pages

## Recommended Build Order

> **Strategy: Per-PRD, phase-ordered.** Build one PRD at a time, but parallelize sub-FSDs within each PRD.
> Frontend pages (PRD-011) can be interleaved — build each page after its backend PRD lands.

| # | PRD | Domain | FSDs | Approach | Depends On |
|---|-----|--------|------|----------|------------|
| 1 | PRD-001 | Platform Infrastructure | FSD-001 | Finish remaining ~20% (CI/CD, monitoring, seed data) | — |
| 2 | PRD-008 | Auth & User Management | FSD-008, 008a-008d | Finish remaining ~60%; parallelize sub-FSDs after main | — |
| | | **— Phase 1 complete —** | | | |
| 3 | PRD-002 | Trendline Detection | FSD-002 | Single FSD, self-contained | Phase 1 |
| 4 | PRD-003 | Trade Execution | FSD-003, 003a-003d | Main FSD first (shared models), then sub-FSDs in parallel | Phase 1 |
| | | **— Phase 2 complete —** | | | |
| 5 | PRD-004 | Trade Journaling | FSD-004 | Single FSD | Phase 2 |
| 6 | PRD-005 | Playbook System | FSD-005 | Single FSD | Phase 2 |
| | | **— Phase 3 complete —** | | | |
| 7 | PRD-010 | Notifications & Integrations | FSD-010, 010a-010c | Parallelize sub-FSDs; only needs Phase 1 | Phase 1 |
| 8 | PRD-006 | Performance Analytics | FSD-006, 006a-006c | Main FSD first, then sub-FSDs in parallel | Phase 3 |
| 9 | PRD-007 | AI Features | FSD-007 | Single FSD | Phase 3 |
| | | **— Phase 4 complete —** | | | |
| 10 | PRD-009 | Billing & Subscriptions | FSD-009, 009a-009c | Parallelize sub-FSDs | Phase 1 |
| | | **— Phase 5 complete —** | | | |
| 11 | PRD-011 | Frontend Dashboard | FSD-011, 011a-011e | Interleave with backend — build pages as backends land | Phases 1-5 |

### Why this order?

- **PRD-001 + PRD-008 first**: Everything else depends on infra and auth being solid.
- **PRD-002 before PRD-003**: Trendline detection feeds signals into trade execution.
- **PRD-004 + PRD-005 after execution**: Journaling and playbooks consume trade data.
- **PRD-010 early (after Phase 1)**: Notifications are independent of trading features — can start as soon as infra is ready.
- **PRD-006 + PRD-007 late**: Analytics and AI need trade data to be meaningful.
- **PRD-009 late**: Billing/gating isn't needed until features exist to gate.
- **PRD-011 interleaved**: Don't save all frontend for the end — build each page right after its backend lands.
