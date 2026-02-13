# TrendEdge — AI-Powered Futures Trading Platform

Trendline detection, automated execution, trade journaling, and performance analytics in one SaaS platform. Built for futures swing traders (1H–Daily timeframes) using the Tori Trades A+ trendline methodology.

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Next.js 14+ (App Router), TypeScript 5.3+, Tailwind 3.4+, shadcn/ui | Vercel hosting, RSC by default |
| Charting | TradingView Lightweight Charts 4.x, D3.js 7.x, Recharts | Financial + analytics charts |
| State | Zustand 4.x, TanStack Query 5.x | Client state + server cache |
| Forms | React Hook Form + Zod | Schema validation |
| Backend | FastAPI (Python 3.12+), async SQLAlchemy 2.0+, Pydantic v2 | Railway hosting |
| Database | PostgreSQL 16 (Supabase), Alembic migrations | RLS enforced on all user tables |
| Cache | Redis (Upstash, TLS via rediss://) | Sliding window rate limits, pub/sub |
| Task Queue | Celery + Redis broker | Queues: high, default, low, notifications, market_data, detection, alerts |
| Auth | Supabase Auth (JWT, OAuth, magic links) | httpOnly cookies, 15-min access / 7-day refresh |
| AI | Anthropic Claude API (claude-sonnet-4-20250514) | Conversational analytics, trade reviews |
| ML | scikit-learn, XGBoost/LightGBM | Trendline scoring, false breakout filter |
| Trendline Engine | scipy.signal, NumPy, pandas | find_peaks + RANSAC fitting |
| Broker APIs | ib_async (IBKR), httpx (Tradovate), Webull SDK (P2) | Common BrokerAdapter ABC |
| Notifications | python-telegram-bot, Discord webhooks, SendGrid | Event-driven via Redis pub/sub |
| Storage | Cloudflare R2 (S3-compatible) | Screenshots, exports, avatars |
| Monitoring | Sentry (errors), Axiom (logs), Uptime Robot | Structured JSON logging only |

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # FastAPI route modules
│   ├── core/            # Config, security, middleware, exceptions, logging
│   ├── db/              # Session factory, ORM models, repositories
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # Business logic layer
│   ├── tasks/           # Celery task definitions
│   └── adapters/        # Broker interfaces (IBKR, Tradovate, Webull)
├── alembic/             # Database migrations
├── tests/               # Unit, integration, e2e
├── Dockerfile
└── docker-compose.yml   # Local dev: PostgreSQL 16, Redis 7, API, Worker, Beat
frontend/                # Next.js App Router
_docs/
├── prd/                 # Product Requirements (PRD-001 through PRD-011)
└── fsd/                 # Functional Specifications (FSD-001 through FSD-011e)
```

## Local Development

- `make dev` → `docker compose up` — full local stack (PostgreSQL, Redis, API, Worker, Beat)
- All 5 services healthy within 60 seconds
- Local DB on port 5432, Redis on 6379, API on localhost:8000
- Environments: local (Docker) → staging (Supabase + Upstash) → prod (Supabase + Upstash)

## Architecture Decisions

- **BFF pattern**: Next.js API routes proxy to FastAPI — browser never calls FastAPI directly
- **RLS everywhere**: PostgreSQL Row-Level Security on all user-owned tables; `auth.uid() = user_id`
- **Service role**: Only for Celery workers, Stripe webhooks, data export — never from frontend
- **Broker encryption**: AES-256-GCM with HKDF-SHA256 per-connection key derivation
- **Event-driven notifications**: Domain events → Redis pub/sub → Celery → channel adapters
- **Feature gating**: YAML config (not runtime-editable), cached in Redis (60s TTL), middleware checks every request
- **Paper-first**: All new users start in paper mode; identical code paths as live trading
- **Graceful degradation**: Core platform functions without AI services; Redis down → sync fallback

## API Conventions

- Versioned endpoints: `/api/v1/`
- Standard error format: `{error: {code, message, details, request_id, timestamp}}`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `RATE_LIMITED`, `BROKER_ERROR`, `SERVICE_UNAVAILABLE`
- Never leak stack traces — full context goes to Sentry only
- Webhooks: HMAC-SHA256 signature verification, idempotent processing via event ID dedup
- Rate limiting: Redis sliding window (sorted sets), per-user per-endpoint
- WebSocket: `/api/v1/ws`, JWT as query param, 30s heartbeat, exponential backoff reconnect

## Database Conventions

- Tables/columns: lowercase `snake_case` (e.g., `broker_connections`, `created_at`)
- Materialized views: `mv_` prefix (e.g., `mv_daily_pnl`, `mv_metrics_cache`)
- Triggers: `on_` prefix (e.g., `on_auth_user_created`, `on_trade_close`)
- Connection: Supavisor port 6543 (transaction mode) for runtime; port 5432 for migrations only
- Pool: 10 (API), 5 (workers), statement_cache_size=0, timeout=30s
- JSONB for flexible metadata: trade context, playbook rules, compliance checklists, annotations

## Redis Key Patterns

- Cache: `cache:{endpoint}:{user_id}:{param_hash}` (TTL: 60–300s)
- Rate limits: `ratelimit:{category}:{identifier}` (sliding window)
- Locks: `lock:{resource}` (30s auto-expire)
- WebSocket pub/sub: `ws:{channel}:{user_id}`
- Circuit breaker: `circuit_breaker:{channel}`
- Tier features: `user:{user_id}:tier_features` (60s TTL)

## Subscription Tiers

```
Free:   $0   — 3 instruments (delayed), paper only, email notifications, 10 journal/mo
Trader: $49  — 10 instruments, 1 broker, 5 playbooks, Telegram + email
Pro:    $99  — Unlimited instruments, 3 brokers, AI features, all channels
Team:   $199 — Unlimited everything, custom webhooks, team analytics
```

## Coding Patterns

- **Backend**: Service layer for business logic, repositories for data access, Pydantic for I/O validation
- **Frontend**: Server Components by default, Client Components only for interactivity
- **Middleware stack** (order matters): RequestID → Timing → CORS → RateLimit → RequestLogging → Sentry
- **Logging**: Structured JSON only — timestamp, level, logger, message, request_id, user_id, duration_ms
- **Secrets**: NEVER log passwords, API keys, JWTs, broker credentials, credit card numbers
- **Retry**: Exponential backoff (1s, 2s, 4s) with max 3 retries for transient errors
- **Circuit breaker**: Trip after 3 consecutive broker failures, 15-min cooldown
- **Idempotency**: Signal dedup (5-min window, 2-tick tolerance), webhook event ID tracking

## Key Domain Concepts

- **A+ Trendline**: ≥3 touches, <45° slope, ≥6-candle spacing, ≥3 weeks duration
- **Safety Line Stop**: Opposite trendline projected +4 candles from break
- **Take Profit**: First S/R level at ≥2R reward; fallback: entry ± (stop_distance × 2.5)
- **R-Multiple**: (actual_pnl) / (planned_risk) — core performance metric
- **MAE/MFE**: Maximum Adverse/Favorable Excursion — tick-level tracking
- **Playbook**: Named strategy container with auto-classification rules and independent metrics
- **Composite Score**: `touch_count × spacing_quality × log2(duration_weeks + 1) × (1 - slope/90)`

## Testing

- Backend: `pytest` with async fixtures, test DB, test Redis
- Frontend: Jest (unit), Playwright (e2e), axe-core (a11y), Lighthouse CI (perf)
- Commands: `make test`, `make lint`, `make migrate`, `make seed`

## Documentation Reference

All detailed specifications live in `_docs/`:
- **PRD-001–011**: Product requirements per feature domain
- **FSD-001–011e**: Functional specs with schemas, endpoints, state machines, error handling
- **00-Technical_Spec_Writing_Guide_v2.md**: Documentation standards

When implementing a feature, always read the corresponding FSD first — it contains exact field names, validation rules, error messages, state transitions, and edge cases.

## Implementation Progress

> Source of truth: `progress.md` (detailed) — this table is the summary view. Agents must update both.
> Frontend is built as **vertical slices** per phase (no separate frontend phase). Each phase includes its matching FSD-011x sub-spec.

| Phase | PRDs/FSDs | Domain | Status | Notes |
|-------|-----------|--------|--------|-------|
| 1 | 001 | Platform Infrastructure | ~95% | CI/CD, tests, seed data done; Axiom/Uptime Robot external config remains |
| 1 | 008 | Auth & User Management | ~85% | Phase 1-2 done: full auth, profiles, broker connections, API keys, RBAC; Phase 3 remains (teams, onboarding, account deletion) |
| 1 | FSD-011a | Frontend: App Shell & Navigation | ~50% | App shell, sidebar, header, providers, design tokens done; cmd palette remains |
| 2 | 002 | Trendline Detection | ~98% | Beat schedule, state transitions, proximity decay, route alignment, 16 integration tests done; IBKR live feed P2 |
| 2 | 003 | Trade Execution | ~98% | All backend complete: 11 tables, 3 services (46 methods), 16+ endpoints, 3 Celery tasks, PaperBrokerAdapter, 91 tests; frontend wired to live API; IBKR/Tradovate live adapters Phase 2 |
| 2 | FSD-011b | Frontend: Dashboard & Trendline Views | ~85% | Dashboard home + trendline page done (mock data); sidebar updated; live API integration remains |
| 3 | 004 | Trade Journaling | not started | |
| 3 | 005 | Playbook System | not started | |
| 3 | FSD-011c | Frontend: Execution & Journal Views | ~90% | Execution page done (7 components wired to live API, SL/TP modify, risk dots); Journal page components done but API integration blocked on FSD-004 |
| 4 | 006 | Performance Analytics | not started | |
| 4 | 007 | AI Features | not started | |
| 4 | FSD-011d | Frontend: Analytics & Playbook Views | not started | |
| 5 | 009 | Billing & Subscriptions | not started | |
| 5 | 010 | Notifications & Integrations | not started | |
| 5 | FSD-011e | Frontend: Settings, Onboarding & AI Chat | not started | |
