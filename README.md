# TrendEdge

AI-powered futures trading platform for swing traders. Trendline detection, automated execution, trade journaling, and performance analytics — built around the Tori Trades A+ trendline methodology.

## What It Does

- **Trendline Detection** — Automatically identifies A+ trendlines (3+ touches, proper slope/spacing/duration) using scipy peak detection and RANSAC fitting, with composite scoring and quality grading
- **Trade Execution** — Signal ingestion, risk management, bracket orders, and position tracking across multiple brokers (IBKR, Tradovate, Webull)
- **Trade Journaling** — Auto-populated journal entries with MAE/MFE tracking, screenshots, tags, and CSV/PDF export
- **Playbook System** — Named strategy containers with auto-classification rules, per-playbook metrics, and rule compliance tracking
- **Performance Analytics** — 30+ metrics across 7 categories, Monte Carlo simulations, correlation analysis, and materialized view aggregation
- **AI Features** — Claude-powered conversational analytics, trade review assistant, ML trendline scoring, and false breakout filtering

## Tech Stack

**Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, TradingView Lightweight Charts, Recharts, Zustand, TanStack Query

**Backend:** FastAPI (Python 3.12+), async SQLAlchemy 2.0, Pydantic v2, Celery + Redis broker

**Data:** PostgreSQL 16 (Supabase) with RLS, Redis (Upstash), Cloudflare R2

**Auth:** Supabase Auth (JWT, OAuth, magic links)

**AI/ML:** Anthropic Claude API, scikit-learn, XGBoost/LightGBM

**Infra:** Docker Compose (local), Vercel (frontend), Railway (backend), GitHub Actions CI/CD

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # FastAPI route modules
│   ├── core/            # Config, security, middleware, logging
│   ├── db/              # Session factory, ORM models, repositories
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # Business logic layer
│   ├── tasks/           # Celery task definitions
│   └── adapters/        # Broker interfaces
├── alembic/             # Database migrations
├── tests/
├── Dockerfile
├── docker-compose.yml
└── Makefile

frontend/                # Next.js App Router
├── src/
│   ├── app/             # Pages and layouts
│   ├── components/      # UI components
│   ├── lib/             # API client, stores, hooks, utils
│   └── types/           # TypeScript definitions
└── package.json

_docs/
├── prd/                 # Product requirements (PRD-001 – PRD-011)
└── fsd/                 # Functional specifications (FSD-001 – FSD-011e)
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.12+

### Local Development

**Backend** (PostgreSQL, Redis, API, Celery Worker, Celery Beat):

```bash
cd backend
make dev          # docker compose up — full stack on localhost:8000
```

All 5 services should be healthy within 60 seconds. PostgreSQL on port 5432, Redis on 6379, API on 8000.

**Frontend:**

```bash
cd frontend
npm install
npm run dev       # Next.js dev server on localhost:3000
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL` (PostgreSQL connection string)
- `REDIS_URL` (Upstash TLS connection)
- `ANTHROPIC_API_KEY` (Claude API)
- `SENTRY_DSN` (error monitoring)

### Common Commands

```bash
# Backend
make dev          # Start all services
make dev-build    # Rebuild and start
make dev-down     # Stop all services
make test         # Run pytest with coverage
make lint         # Ruff + mypy
make migrate      # Run Alembic migrations
make seed         # Seed demo data (4 users + audit logs)

# Frontend
npm run dev       # Dev server
npm run build     # Production build
npm run lint      # ESLint
```

## Architecture

- **BFF pattern** — Next.js API routes proxy to FastAPI; the browser never calls FastAPI directly
- **RLS everywhere** — PostgreSQL Row-Level Security on all user-owned tables
- **Paper-first** — All new users start in paper trading mode with identical code paths to live
- **Event-driven** — Domain events flow through Redis pub/sub to Celery workers to notification channels
- **Graceful degradation** — Core platform works without AI services; Redis down triggers sync fallback

## Subscription Tiers

| Tier | Price | Highlights |
|------|-------|------------|
| Free | $0/mo | 3 instruments (delayed), paper only, 10 journal entries/mo |
| Trader | $49/mo | 10 instruments, 1 broker, 5 playbooks, Telegram alerts |
| Pro | $99/mo | Unlimited instruments, 3 brokers, AI features, all channels |
| Team | $199/mo | Everything unlimited, custom webhooks, team analytics |

## Development Status

~30% complete. Infrastructure, auth, and trendline detection are built. See [PROGRESS.md](PROGRESS.md) for detailed tracking.

| Domain | Status |
|--------|--------|
| Platform Infrastructure | ~95% |
| Trendline Detection | ~98% |
| Auth & User Management | ~85% |
| Frontend Shell & Dashboard | ~50% |
| Trade Execution | Not started |
| Journaling, Playbooks, Analytics, AI, Billing, Notifications | Not started |

## License

Proprietary. All rights reserved.
