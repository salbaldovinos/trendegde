# PRD-001: Platform Infrastructure & DevOps

**TrendEdge -- AI-Powered Futures Trading Platform**

| Field | Value |
|---|---|
| PRD ID | PRD-001 |
| Title | Platform Infrastructure & DevOps |
| Version | 1.0 |
| Status | Draft |
| Author | TrendEdge Engineering |
| Created | 2026-02-11 |
| Last Updated | 2026-02-11 |
| Classification | CONFIDENTIAL |

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [User Stories](#3-user-stories)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [DevOps Requirements](#6-devops-requirements)
7. [Security Requirements](#7-security-requirements)
8. [Dependencies](#8-dependencies)
9. [Testing Requirements](#9-testing-requirements)
10. [Acceptance Criteria](#10-acceptance-criteria)
11. [Phase Mapping](#11-phase-mapping)
12. [Cross-References](#12-cross-references-to-other-prds)
13. [Appendix](#13-appendix)

---

## 1. Overview & Purpose

### 1.1 What This PRD Covers

This document specifies the foundational platform infrastructure, DevOps practices, and security architecture for TrendEdge. It defines every service, deployment pipeline, environment, database configuration, and operational standard that all other product features depend on.

**This PRD is the foundation layer.** No feature PRD (PRD-002 through PRD-011) can be implemented without the infrastructure defined here being operational. It covers:

- Backend application scaffold (FastAPI on Railway)
- Frontend hosting (Next.js on Vercel)
- Database architecture (Supabase PostgreSQL)
- Caching and message broker (Upstash Redis)
- Task queue system (Celery workers)
- WebSocket real-time layer
- CI/CD pipelines (GitHub Actions)
- Monitoring, alerting, and observability
- Security posture and compliance
- Environment management (dev/staging/prod)

### 1.2 What This PRD Does NOT Cover

- Trendline detection algorithms (PRD-003)
- Broker adapter implementations (PRD-004)
- Trade execution logic (PRD-005)
- UI/UX design (PRD-007)
- AI/ML model architecture (PRD-009)

### 1.3 Role in the Larger System

TrendEdge's product architecture follows a layered dependency model:

```
Layer 4: User-Facing Features
            PRD-007 Dashboard UI
            PRD-008 Notifications
            PRD-010 Billing & Subscription

Layer 3: Domain Logic
            PRD-003 Trendline Detection Engine
            PRD-004 Broker Adapters
            PRD-005 Trade Execution Pipeline
            PRD-006 Journaling & Playbooks
            PRD-009 AI/ML Features
            PRD-011 Analytics Engine

Layer 2: Data Layer
            PRD-002 Data Models & Database Schema

Layer 1: Infrastructure (THIS PRD)
            PRD-001 Platform Infrastructure & DevOps
```

Every layer above depends on Layer 1. This PRD must be implemented first and must remain stable throughout the product lifecycle.

### 1.4 Design Principles

1. **Cost-conscious by default.** Target $50-120/mo for MVP. Every service choice must justify its cost at the current scale.
2. **Single-developer operable.** The entire stack must be manageable by one engineer. No Kubernetes. No self-managed databases. Managed services only.
3. **Paper-trade-safe.** Infrastructure must treat paper trading and live trading with identical reliability. A bug in paper mode is a bug in production.
4. **Latency-aware, not latency-obsessed.** The target is 1H+ timeframe strategies. Sub-second execution is not required. Sub-10-second webhook-to-order is.
5. **Fail loud, fail safe.** Every failure must produce an alert. No silent data loss. No silent order failures. Circuit breakers over silent retries.

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
                         +------------------+
                         |   Cloudflare     |
                         |   DNS + CDN      |
                         +--------+---------+
                                  |
                    +-------------+-------------+
                    |                           |
           +--------v--------+        +--------v--------+
           |   Vercel         |        |   Railway        |
           |   (Frontend)     |        |   (Backend)      |
           |                  |        |                  |
           |  Next.js 14+     |        |  FastAPI         |
           |  App Router      |        |  Python 3.12+    |
           |  TypeScript      |        |  Uvicorn         |
           |  Tailwind CSS    |        |  Gunicorn        |
           |  shadcn/ui       |        |                  |
           +--------+---------+        +---+---------+----+
                    |                      |         |
                    |    REST/WS           |         |
                    +----------+-----------+         |
                               |                     |
                    +----------v-----------+         |
                    |   Supabase            |         |
                    |   (Data Platform)     |         |
                    |                       |         |
                    |  PostgreSQL 16        |         |
                    |  Supabase Auth        |         |
                    |  Supabase Storage     |         |
                    |  Supavisor (Pooling)  |         |
                    |  Edge Functions       |         |
                    +-----------------------+         |
                                                      |
                    +----------v-----------+          |
                    |   Upstash Redis       <----------+
                    |   (Serverless)        |
                    |                       |
                    |  Cache Layer          |
                    |  Celery Broker        |
                    |  Pub/Sub              |
                    |  Rate Limiting        |
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    |   Railway              |
                    |   (Celery Workers)     |
                    |                        |
                    |  Trendline Scans       |
                    |  Alert Evaluation      |
                    |  Notification Dispatch |
                    |  AI/ML Jobs            |
                    +------------------------+

          Monitoring & Observability
          +-----------+  +-----------+  +---------------+
          |  Sentry   |  |  Axiom    |  | Uptime Robot  |
          |  (Errors) |  |  (Logs)   |  | (Health)      |
          +-----------+  +-----------+  +---------------+
```

### 2.2 Service Topology

| Service | Platform | Role | Process Type | Instances (MVP) |
|---|---|---|---|---|
| `trendedge-web` | Vercel | Frontend application | Serverless | Auto-scaled |
| `trendedge-api` | Railway | REST API + WebSocket server | Long-running | 1 |
| `trendedge-worker` | Railway | Celery task worker | Long-running | 1 |
| `trendedge-beat` | Railway | Celery periodic scheduler | Long-running | 1 |
| `trendedge-db` | Supabase | PostgreSQL 16 database | Managed | 1 (Free/Pro) |
| `trendedge-redis` | Upstash | Cache, broker, pub/sub | Serverless | 1 |
| `trendedge-storage` | Supabase Storage | File/blob storage | Managed | 1 |

### 2.3 Communication Patterns

| Pattern | From | To | Protocol | Use Case |
|---|---|---|---|---|
| Synchronous REST | Frontend | API | HTTPS (JSON) | CRUD operations, dashboard data |
| WebSocket | Frontend | API | WSS | Real-time trade updates, trendline alerts |
| Task Queue | API | Worker | Redis (Celery) | Async jobs: scans, notifications, AI |
| Database Query | API/Worker | PostgreSQL | TCP (Supavisor) | Data persistence, queries |
| Pub/Sub | API/Worker | Redis | Redis Pub/Sub | WebSocket fan-out, event broadcast |
| Webhook Inbound | TradingView | API | HTTPS POST | Trade signals |
| Webhook Outbound | API | Telegram/Discord | HTTPS POST | Notifications |
| Storage | API | Supabase Storage | HTTPS (S3 API) | Chart screenshots, exports |

### 2.4 Network Boundaries

```
Public Internet
    |
    +-- Vercel Edge Network (frontend, CDN, SSL termination)
    |
    +-- Railway Public Endpoint (API, SSL termination)
    |       |
    |       +-- Railway Internal Network
    |               +-- API <-> Workers (via Redis, not direct)
    |
    +-- Supabase Cloud (database, auth, storage)
    |       |
    |       +-- Supavisor connection pooler (port 6543)
    |       +-- Direct connection (port 5432, for migrations only)
    |
    +-- Upstash Redis (TLS-encrypted endpoint)
```

---

## 3. User Stories

### 3.1 Developer Stories

| ID | Story | Priority |
|---|---|---|
| INF-US-001 | As a developer, I want a single `docker compose up` command to run the full stack locally so that I can develop without depending on cloud services. | P0 |
| INF-US-002 | As a developer, I want automatic code formatting and linting on commit so that code style is consistent without manual effort. | P0 |
| INF-US-003 | As a developer, I want database migrations to run automatically on deploy so that schema changes are applied without manual SQL execution. | P0 |
| INF-US-004 | As a developer, I want structured JSON logging with request IDs so that I can trace a request across API, worker, and database. | P0 |
| INF-US-005 | As a developer, I want hot-reload in both frontend and backend during local development so that feedback loops are under 2 seconds. | P1 |
| INF-US-006 | As a developer, I want environment-specific configuration with zero code changes between dev, staging, and prod. | P0 |
| INF-US-007 | As a developer, I want auto-generated API documentation from code annotations so that the API is always accurately documented. | P1 |
| INF-US-008 | As a developer, I want a seed script that populates the local database with realistic test data so that UI development has meaningful data to render. | P1 |

### 3.2 Operator Stories

| ID | Story | Priority |
|---|---|---|
| INF-US-009 | As an operator, I want health check endpoints for every service so that Uptime Robot can alert me within 60 seconds of a failure. | P0 |
| INF-US-010 | As an operator, I want all errors reported to Sentry with full context so that I can diagnose production issues without SSH access. | P0 |
| INF-US-011 | As an operator, I want deployment to production triggered by merging to `main` so that releases are automated and auditable. | P0 |
| INF-US-012 | As an operator, I want database backups to run daily with 7-day retention so that data loss is limited to at most 24 hours. | P0 |
| INF-US-013 | As an operator, I want a staging environment that mirrors production so that I can validate changes before they affect live trading. | P1 |
| INF-US-014 | As an operator, I want resource usage alerts (CPU >80%, memory >85%, disk >90%) so that I can scale before users are impacted. | P1 |
| INF-US-015 | As an operator, I want a single dashboard showing all service health, error rates, and latency percentiles. | P1 |

### 3.3 Security Stories

| ID | Story | Priority |
|---|---|---|
| INF-US-016 | As a user, I want all API communication encrypted via TLS so that my trading data and credentials are never transmitted in plaintext. | P0 |
| INF-US-017 | As a user, I want my broker credentials stored with encryption at rest so that a database breach does not expose my brokerage account. | P0 |
| INF-US-018 | As a user, I want rate limiting on authentication endpoints so that brute-force attacks against my account are mitigated. | P0 |

---

## 4. Functional Requirements

### 4.1 FastAPI Application Scaffold

#### INF-FR-001: Project Structure

The backend MUST follow this directory structure:

```
backend/
|-- app/
|   |-- __init__.py
|   |-- main.py                  # FastAPI app factory, lifespan events
|   |-- config.py                # Pydantic Settings (env-based config)
|   |-- dependencies.py          # Shared FastAPI dependencies (db, redis, auth)
|   |
|   |-- api/
|   |   |-- __init__.py
|   |   |-- v1/
|   |   |   |-- __init__.py
|   |   |   |-- router.py        # Aggregated v1 router
|   |   |   |-- health.py        # Health check endpoints
|   |   |   |-- webhooks.py      # TradingView webhook receiver
|   |   |   |-- trades.py        # Trade CRUD
|   |   |   |-- trendlines.py    # Trendline CRUD + alerts
|   |   |   |-- playbooks.py     # Playbook management
|   |   |   |-- analytics.py     # Analytics queries
|   |   |   |-- journal.py       # Journal entries
|   |   |   |-- users.py         # User profile & settings
|   |   |   |-- ws.py            # WebSocket endpoints
|   |
|   |-- core/
|   |   |-- __init__.py
|   |   |-- security.py          # JWT validation, API key verification
|   |   |-- middleware.py         # CORS, logging, timing, rate limit
|   |   |-- exceptions.py        # Custom exception classes + handlers
|   |   |-- logging.py           # Structured logging configuration
|   |
|   |-- db/
|   |   |-- __init__.py
|   |   |-- session.py           # Async SQLAlchemy session factory
|   |   |-- base.py              # Declarative base
|   |   |-- models/              # SQLAlchemy ORM models
|   |   |-- repositories/        # Data access layer (repository pattern)
|   |
|   |-- schemas/
|   |   |-- __init__.py
|   |   |-- requests/            # Pydantic request models
|   |   |-- responses/           # Pydantic response models
|   |
|   |-- services/
|   |   |-- __init__.py
|   |   |-- trade_service.py     # Business logic layer
|   |   |-- trendline_service.py
|   |   |-- notification_service.py
|   |
|   |-- tasks/
|   |   |-- __init__.py
|   |   |-- celery_app.py        # Celery application factory
|   |   |-- trendline_tasks.py   # Trendline scan + alert tasks
|   |   |-- notification_tasks.py
|   |   |-- analytics_tasks.py
|   |
|   |-- adapters/
|   |   |-- __init__.py
|   |   |-- broker_base.py       # Abstract BrokerInterface
|   |   |-- ibkr_adapter.py
|   |   |-- tradovate_adapter.py
|   |
|   |-- utils/
|       |-- __init__.py
|       |-- symbols.py           # Continuous symbol mapping (NQ1! -> MNQ)
|       |-- time.py              # Session time helpers, timezone utils
|
|-- alembic/
|   |-- env.py
|   |-- versions/                # Migration files
|
|-- tests/
|   |-- conftest.py              # Fixtures: test db, client, auth
|   |-- unit/
|   |-- integration/
|   |-- e2e/
|
|-- alembic.ini
|-- pyproject.toml               # Dependencies, tool config (ruff, pytest)
|-- Dockerfile
|-- docker-compose.yml           # Local dev: postgres, redis, api, worker
|-- Makefile                     # Common commands
|-- .env.example
```

**Acceptance:** Running `make dev` starts the full local stack. Running `make test` executes the test suite. Running `make lint` checks code quality.

#### INF-FR-002: Middleware Stack

The FastAPI application MUST include the following middleware, applied in this order (outermost first):

| Order | Middleware | Purpose | Configuration |
|---|---|---|---|
| 1 | `RequestIDMiddleware` | Assign UUID to every request; propagate in headers and logs | Header: `X-Request-ID` |
| 2 | `TimingMiddleware` | Measure and log request duration | Log field: `duration_ms` |
| 3 | `CORSMiddleware` | Cross-origin resource sharing | See INF-FR-012 |
| 4 | `RateLimitMiddleware` | Per-endpoint rate limiting | See INF-SEC-004 |
| 5 | `RequestLoggingMiddleware` | Log method, path, status, duration, user_id | See INF-FR-013 |
| 6 | `SentryMiddleware` | Capture unhandled exceptions | DSN from env |

#### INF-FR-003: Error Handling

All API errors MUST return a consistent JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      {
        "field": "entry_price",
        "message": "Must be a positive number"
      }
    ],
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-02-11T10:30:00Z"
  }
}
```

Standard error codes:

| HTTP Status | Error Code | Description |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request body/params failed validation |
| 401 | `AUTHENTICATION_REQUIRED` | Missing or invalid JWT |
| 403 | `FORBIDDEN` | Valid JWT but insufficient permissions |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Duplicate resource or state conflict |
| 422 | `UNPROCESSABLE_ENTITY` | Valid syntax but semantic error (e.g., invalid symbol) |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unhandled server error (logged to Sentry) |
| 502 | `BROKER_ERROR` | Upstream broker API failure |
| 503 | `SERVICE_UNAVAILABLE` | Dependency down (DB, Redis, broker) |

**Requirement:** 5xx errors MUST NOT leak stack traces, internal paths, or database details to the client. Full context MUST be sent to Sentry.

### 4.2 Supabase PostgreSQL Setup

#### INF-FR-004: Connection Management

| Parameter | Value | Notes |
|---|---|---|
| Connection method | Supavisor (transaction mode) | Port 6543 for application queries |
| Direct connection | Port 5432 | Migrations and admin tasks only |
| Connection pool size | 10 (API), 5 (worker) | Supabase Free: 60 direct connections max |
| ORM | SQLAlchemy 2.0+ (async) | `asyncpg` driver for async operations |
| Session management | Scoped async session per request | Dependency injection via FastAPI `Depends()` |
| Statement timeout | 30 seconds | Prevent runaway queries |
| Idle connection timeout | 300 seconds | Reclaim unused connections |

**Implementation:**

```python
# Async engine with Supavisor connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+asyncpg://...@db.xxx.supabase.co:6543/postgres
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"statement_cache_size": 0},  # Required for Supavisor
)
```

#### INF-FR-005: Migration Strategy

| Aspect | Decision |
|---|---|
| Migration tool | Alembic (SQLAlchemy-native) |
| Migration naming | `YYYY_MM_DD_HHMM_<description>.py` (e.g., `2026_02_15_1430_create_trades_table.py`) |
| Auto-generation | `alembic revision --autogenerate -m "description"` from model changes |
| Migration execution | Automatic on deploy (GitHub Actions runs `alembic upgrade head` before service restart) |
| Rollback strategy | Each migration MUST include a `downgrade()` function. Test both directions. |
| Data migrations | Separate from schema migrations. Use explicit data migration scripts. |
| Production safeguard | Migrations run against staging first. Production requires manual approval gate in CI. |

**Branching rule:** Only one migration per PR. Conflicting migrations MUST be resolved before merge.

#### INF-FR-006: Database Backup Strategy

| Tier | Backup Method | Frequency | Retention | RPO | RTO |
|---|---|---|---|---|---|
| Supabase Free | Supabase daily backups | Daily | 7 days | 24 hours | 1 hour |
| Supabase Pro ($25/mo) | Point-in-time recovery | Continuous (WAL) | 7 days | Minutes | 30 min |
| Custom supplement | `pg_dump` via GitHub Actions cron | Daily | 30 days (R2) | 24 hours | 2 hours |

Phase 1 uses Supabase Free tier backups supplemented by a nightly `pg_dump` to Cloudflare R2 or Supabase Storage.

### 4.3 Redis Configuration (Upstash)

#### INF-FR-007: Redis Usage Patterns

| Usage | Key Pattern | TTL | Serialization | Example |
|---|---|---|---|---|
| API response cache | `cache:{endpoint}:{hash}` | 60-300s | JSON | `cache:analytics:user123:abc` |
| Rate limiting | `ratelimit:{category}:{user_id}` | Window-based | Counter | `ratelimit:webhook:user123` |
| Celery broker | `celery` (managed by Celery) | Task-dependent | Pickle/JSON | Celery default keys |
| Celery result backend | `celery-task-meta-*` | 3600s | JSON | Task results |
| WebSocket pub/sub | `ws:{channel}:{user_id}` | N/A (pub/sub) | JSON | `ws:trades:user123` |
| Session/dedup | `dedup:webhook:{hash}` | 60s | String | Prevent duplicate webhook processing |
| Distributed locks | `lock:{resource}` | 30s | String | `lock:trendline_scan:PL` |

#### INF-FR-008: Redis Connection Configuration

```python
# Upstash Redis configuration
UPSTASH_REDIS_URL = "rediss://default:xxx@us1-xxx.upstash.io:6379"

# Connection settings
redis_client = Redis.from_url(
    settings.UPSTASH_REDIS_URL,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    max_connections=20,
)
```

**Cost consideration:** Upstash charges per command. Avoid patterns that generate excessive commands (e.g., polling loops, key scans). Use pub/sub for real-time instead of polling. Target <10,000 commands/day for MVP ($0 -- free tier covers 10K commands/day).

### 4.4 Celery Worker Configuration

#### INF-FR-009: Queue Architecture

| Queue Name | Worker Concurrency | Purpose | Priority |
|---|---|---|---|
| `high` | 2 (prefork) | Trade execution, order management, webhook processing | P0 |
| `default` | 4 (prefork) | Trendline scans, alert evaluation, analytics updates | P0 |
| `low` | 2 (prefork) | AI analysis, report generation, data backfill | P1 |
| `notifications` | 2 (prefork) | Telegram, Discord, email dispatch | P0 |

**MVP simplification:** A single worker process handles all queues with a combined concurrency of 4. Queues are separated logically for future scaling.

#### INF-FR-010: Celery Configuration

```python
# celery_app.py
celery_app = Celery("trendedge")

celery_app.conf.update(
    broker_url=settings.UPSTASH_REDIS_URL,
    result_backend=settings.UPSTASH_REDIS_URL,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,               # Re-deliver if worker crashes
    worker_prefetch_multiplier=1,       # Fair scheduling
    task_reject_on_worker_lost=True,
    result_expires=3600,                # 1 hour result TTL
    worker_max_tasks_per_child=200,     # Prevent memory leaks
    worker_max_memory_per_child=512_000, # 512MB memory limit per child
    broker_transport_options={
        "visibility_timeout": 600,      # 10 min for long tasks
    },
)
```

#### INF-FR-011: Task Retry Policies

| Task Category | Max Retries | Backoff | Retry Delay | Dead Letter |
|---|---|---|---|---|
| Webhook processing | 3 | Exponential | 5s, 25s, 125s | Log to DB + Sentry alert |
| Broker API calls | 5 | Exponential + jitter | 2s, 8s, 32s, 128s, 512s | Circuit breaker (see below) |
| Trendline scan | 2 | Fixed | 60s | Log, retry on next schedule |
| Notification dispatch | 3 | Exponential | 10s, 60s, 300s | Log to DB, skip |
| AI/ML tasks | 1 | None | N/A | Log, manual retry |

**Circuit Breaker:** After 3 consecutive broker API failures within 5 minutes, halt all execution tasks for that broker for 10 minutes. Send Telegram alert to operator. Resume automatically and send confirmation.

### 4.5 WebSocket Support

#### INF-FR-012: WebSocket Architecture

```
Client (Browser)
    |
    | WSS connection (authenticated with JWT)
    |
FastAPI WebSocket endpoint (/api/v1/ws)
    |
    | Subscribe to Redis pub/sub channels
    |
Upstash Redis Pub/Sub
    ^
    |
    | Publish events from:
    |   - API request handlers (trade created, updated)
    |   - Celery workers (trendline alert, scan complete)
    |   - Broker adapters (fill received, order status)
```

**WebSocket Event Types:**

| Event | Channel | Payload Summary |
|---|---|---|
| `trade.created` | `ws:trades:{user_id}` | Trade ID, instrument, direction, entry price |
| `trade.updated` | `ws:trades:{user_id}` | Trade ID, updated fields (fill, P&L, status) |
| `trade.closed` | `ws:trades:{user_id}` | Trade ID, final P&L, R-multiple |
| `trendline.alert` | `ws:trendlines:{user_id}` | Trendline ID, alert type, instrument, price |
| `trendline.new` | `ws:trendlines:{user_id}` | New qualifying trendline details |
| `scan.complete` | `ws:system:{user_id}` | Scan results summary |
| `system.health` | `ws:system:{user_id}` | Service status updates |

**Connection Management:**
- Heartbeat ping every 30 seconds
- Auto-reconnect on client side with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- Maximum 10 concurrent WebSocket connections per user
- JWT re-validation every 15 minutes on open connections

### 4.6 Environment Configuration Management

#### INF-FR-013: Configuration Architecture

All configuration MUST flow through Pydantic Settings with environment variable binding. No hardcoded values for any environment-specific setting.

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    # Redis
    UPSTASH_REDIS_URL: str

    # Supabase Auth
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Broker credentials (encrypted at rest)
    IBKR_HOST: str = ""
    IBKR_PORT: int = 4002
    TRADOVATE_API_KEY: str = ""
    TRADOVATE_API_SECRET: str = ""

    # External services
    SENTRY_DSN: str = ""
    AXIOM_API_TOKEN: str = ""
    TELEGRAM_BOT_TOKEN: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Rate limiting
    RATE_LIMIT_DEFAULT: int = 100  # requests per minute

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"
```

#### INF-FR-014: Environment Matrix

| Setting | Development | Staging | Production |
|---|---|---|---|
| `APP_ENV` | `development` | `staging` | `production` |
| `APP_DEBUG` | `true` | `false` | `false` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` |
| Database | Local PostgreSQL (Docker) | Supabase (staging project) | Supabase (prod project) |
| Redis | Local Redis (Docker) | Upstash (staging instance) | Upstash (prod instance) |
| Broker mode | Paper (simulated fills) | Paper (real broker API) | Live + Paper |
| Sentry | Disabled | Enabled (10% sample) | Enabled (100% sample) |
| CORS origins | `localhost:3000` | `staging.trendedge.app` | `app.trendedge.app` |
| API docs | Enabled (`/docs`) | Enabled (`/docs`) | Disabled |

### 4.7 Health Check Endpoints

#### INF-FR-015: Health Check Specification

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/health` | GET | None | Basic liveness probe (returns 200 if process is running) |
| `/health/ready` | GET | None | Readiness probe (checks all dependencies) |
| `/health/detailed` | GET | API Key | Full diagnostic with component status |

**Liveness response (`/health`):**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-02-11T10:30:00Z"
}
```

**Readiness response (`/health/ready`):**

```json
{
  "status": "ok",
  "checks": {
    "database": { "status": "ok", "latency_ms": 12 },
    "redis": { "status": "ok", "latency_ms": 3 },
    "celery": { "status": "ok", "workers": 1 }
  }
}
```

If any dependency is down, return HTTP 503 with `"status": "degraded"` and the failing component.

**Readiness response (degraded):**

```json
{
  "status": "degraded",
  "checks": {
    "database": { "status": "ok", "latency_ms": 12 },
    "redis": { "status": "error", "message": "Connection refused" },
    "celery": { "status": "ok", "workers": 1 }
  }
}
```

### 4.8 API Versioning Strategy

#### INF-FR-016: Versioning Approach

| Aspect | Decision |
|---|---|
| Strategy | URL path prefix versioning (`/api/v1/`, `/api/v2/`) |
| Current version | `v1` |
| Deprecation policy | Minimum 6 months notice before removing a version |
| Version header | `X-API-Version` response header indicates active version |
| Breaking change definition | Removing a field, changing a field type, removing an endpoint, changing auth requirements |
| Non-breaking changes | Adding optional fields, adding endpoints, adding enum values |

**Router setup:**

```python
# main.py
from app.api.v1.router import router as v1_router

app = FastAPI(title="TrendEdge API", version="0.1.0")
app.include_router(v1_router, prefix="/api/v1")
```

### 4.9 CORS Configuration

#### INF-FR-017: CORS Policy

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-API-Key",
    ],
    expose_headers=["X-Request-ID", "X-API-Version", "X-RateLimit-Remaining"],
    max_age=600,  # Preflight cache: 10 minutes
)
```

| Environment | Allowed Origins |
|---|---|
| Development | `http://localhost:3000`, `http://127.0.0.1:3000` |
| Staging | `https://staging.trendedge.app` |
| Production | `https://app.trendedge.app`, `https://trendedge.app` |

### 4.10 Request/Response Logging

#### INF-FR-018: Logging Standards

All log entries MUST be structured JSON (not plaintext) and include these fields:

```json
{
  "timestamp": "2026-02-11T10:30:00.123Z",
  "level": "INFO",
  "logger": "trendedge.api",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/api/v1/webhooks/tradingview",
  "status_code": 200,
  "duration_ms": 45,
  "user_id": "user_abc123",
  "ip": "203.0.113.42",
  "user_agent": "TradingView/1.0"
}
```

**Logging Rules:**

| Rule | Requirement |
|---|---|
| Sensitive data | NEVER log passwords, API keys, JWT tokens, broker credentials, or full credit card numbers |
| Request bodies | Log webhook payloads (redacting secrets). Do NOT log full request bodies for user-data endpoints. |
| Response bodies | Do NOT log response bodies (too verbose). Log status codes and sizes. |
| PII handling | Log `user_id` (opaque UUID). Do NOT log email, name, or IP in analytics logs. IP allowed in access logs with 30-day retention. |
| Log levels | `DEBUG`: detailed diagnostic. `INFO`: request lifecycle, business events. `WARNING`: recoverable issues. `ERROR`: failures requiring attention. `CRITICAL`: system-level failures. |
| Log destination | stdout (captured by Railway/Vercel) -> forwarded to Axiom |

**Axiom Integration:**

- Railway logs forwarded to Axiom via log drain (Railway native integration)
- Vercel logs forwarded via Vercel log drain or Axiom Vercel integration
- Retention: 30 days (Axiom free tier)

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Target | Measurement |
|---|---|---|---|
| INF-NFR-001 | Webhook-to-paper-trade latency | <10 seconds (p95) | Measured from POST received to simulated fill logged |
| INF-NFR-002 | API response time (CRUD endpoints) | <200ms (p95) | Measured at application layer, excluding network |
| INF-NFR-003 | API response time (analytics queries) | <2 seconds (p95) | Complex aggregation queries with caching |
| INF-NFR-004 | WebSocket message delivery | <500ms (p95) | From event publish to client receipt |
| INF-NFR-005 | Dashboard initial load (LCP) | <2.5 seconds | Lighthouse measurement on 4G connection |
| INF-NFR-006 | Trendline scan (single instrument) | <30 seconds | Full scan: data fetch + detection + scoring |
| INF-NFR-007 | Database query time | <100ms (p95) | Simple queries. Indexed. Via connection pool. |

### 5.2 Availability

| ID | Requirement | Target | Notes |
|---|---|---|---|
| INF-NFR-008 | Execution pipeline uptime | 99.5% | ~43 minutes downtime/month allowed. Measured during market hours (Sun 5PM - Fri 4PM CT). |
| INF-NFR-009 | Dashboard availability | 99.0% | ~7.3 hours downtime/month allowed. Non-critical outside trading hours. |
| INF-NFR-010 | Webhook endpoint availability | 99.5% | TradingView retries once. Must be available for the retry. |
| INF-NFR-011 | Planned maintenance windows | Weekends only | Sat 6PM - Sun 3PM CT. No maintenance during futures sessions. |

### 5.3 Scalability

| ID | Requirement | Phase 1 (MVP) | Phase 2 (Growth) | Phase 3 (Scale) |
|---|---|---|---|---|
| INF-NFR-012 | Concurrent users | 1-5 | 50-100 | 500-1,000+ |
| INF-NFR-013 | API requests/minute | 100 | 1,000 | 10,000 |
| INF-NFR-014 | WebSocket connections | 5 | 100 | 1,000 |
| INF-NFR-015 | Celery tasks/minute | 20 | 200 | 2,000 |
| INF-NFR-016 | Database size | <1 GB | <10 GB | <100 GB |
| INF-NFR-017 | Worker instances | 1 | 2-3 | 5-10 |

**Scaling triggers:**
- Add worker instance when task queue backlog > 100 tasks for > 5 minutes
- Upgrade database tier when connection count consistently > 70% of pool
- Add API instance when p95 latency exceeds 500ms for > 10 minutes

### 5.4 Reliability

| ID | Requirement | Target |
|---|---|---|
| INF-NFR-018 | Zero data loss for completed trades | Trades MUST be persisted to database before sending broker confirmation to user |
| INF-NFR-019 | Webhook idempotency | Duplicate webhooks (within 60s window) MUST NOT create duplicate orders |
| INF-NFR-020 | Graceful degradation | If Redis is down: API continues (without caching). If Celery is down: critical tasks (webhooks) processed synchronously. |
| INF-NFR-021 | Database transaction integrity | All trade-related writes (trade + journal + analytics update) MUST be atomic |

### 5.5 Cost Targets

| ID | Phase | Monthly Target | Constraint |
|---|---|---|---|
| INF-NFR-022 | MVP (0-100 users) | $50-120/month | Must use free tiers aggressively |
| INF-NFR-023 | Growth (100-1K users) | $250-500/month | Scale horizontally only when needed |
| INF-NFR-024 | Scale (1K+ users) | $1,000-2,500/month | Cost per user < $2.50/month |

**MVP Cost Breakdown:**

| Service | Plan | Monthly Cost |
|---|---|---|
| Railway (API + Worker + Beat) | Hobby ($5/mo + usage) | $15-30 |
| Supabase (DB + Auth + Storage) | Free tier | $0 |
| Upstash Redis | Free tier (10K cmds/day) | $0 |
| Vercel | Hobby (free) | $0 |
| Sentry | Free tier (5K events/mo) | $0 |
| Axiom | Free tier (500MB ingest/mo) | $0 |
| Uptime Robot | Free tier (50 monitors) | $0 |
| Domain + DNS (Cloudflare) | Free tier + domain | $10-15/year |
| CME data (via broker) | Included with broker | $0-25 |
| Claude API (AI features) | Pay-per-use | $5-20 |
| Telegram Bot API | Free | $0 |
| **Total** | | **$30-90/month** |

---

## 6. DevOps Requirements

### 6.1 GitHub Actions CI/CD Pipelines

#### INF-DEVOPS-001: Pipeline Architecture

```
Push to Feature Branch
    |
    v
[CI: Lint + Type Check + Unit Tests]
    |
    v
Pull Request to main
    |
    v
[CI: Full Test Suite (unit + integration)]
    |
    +-- Review Required (1 approval)
    |
    v
Merge to main
    |
    +----> [CD: Deploy Backend to Railway (staging)]
    |           |
    |           v
    |      [Run Migrations on Staging DB]
    |           |
    |           v
    |      [Smoke Tests against Staging]
    |           |
    |           v
    |      [Manual Approval Gate] (Production only, Phase 2+)
    |           |
    |           v
    |      [CD: Deploy Backend to Railway (production)]
    |           |
    |           v
    |      [Run Migrations on Production DB]
    |           |
    |           v
    |      [Post-Deploy Health Check]
    |
    +----> [CD: Deploy Frontend to Vercel]
                |
                v
           [Vercel Preview -> Production Promotion]
```

#### INF-DEVOPS-002: CI Pipeline -- Lint & Test

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Ruff lint
        run: ruff check .
      - name: Ruff format check
        run: ruff format --check .
      - name: Type check
        run: mypy app/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: trendedge_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run migrations
        run: alembic upgrade head
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/trendedge_test
      - name: Run tests
        run: pytest tests/ -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/trendedge_test
          UPSTASH_REDIS_URL: redis://localhost:6379/0
          APP_ENV: development
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  frontend-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "pnpm"
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm type-check
      - run: pnpm test
```

#### INF-DEVOPS-003: CD Pipeline -- Backend Deploy

```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - "backend/**"
      - ".github/workflows/deploy-backend.yml"

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway (staging)
        uses: railwayapp/nixpacks-action@v1
        with:
          project-id: ${{ secrets.RAILWAY_PROJECT_ID }}
          environment: staging
          service: trendedge-api
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      - name: Run migrations
        run: |
          railway run --service trendedge-api \
            alembic upgrade head
      - name: Smoke test
        run: |
          sleep 10
          curl -f https://staging-api.trendedge.app/health/ready \
            || exit 1

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway (production)
        uses: railwayapp/nixpacks-action@v1
        with:
          project-id: ${{ secrets.RAILWAY_PROJECT_ID }}
          environment: production
          service: trendedge-api
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      - name: Run migrations
        run: |
          railway run --service trendedge-api \
            alembic upgrade head
      - name: Health check
        run: |
          sleep 10
          curl -f https://api.trendedge.app/health/ready \
            || exit 1
      - name: Notify success
        if: success()
        run: |
          curl -X POST "${{ secrets.TELEGRAM_WEBHOOK }}" \
            -d "chat_id=${{ secrets.TELEGRAM_CHAT_ID }}" \
            -d "text=Deployed backend ${{ github.sha }} to production"
```

### 6.2 Environment Management

#### INF-DEVOPS-004: Environment Topology

| Environment | Purpose | Deploy Trigger | Database | URL |
|---|---|---|---|---|
| `development` | Local development | Manual (`docker compose up`) | Local PostgreSQL (Docker) | `localhost:8000` |
| `staging` | Pre-production validation | Auto on merge to `main` | Supabase staging project | `staging-api.trendedge.app` |
| `production` | Live system | Manual approval after staging | Supabase production project | `api.trendedge.app` |

**Phase 1 simplification:** Staging and production share the same Railway project with separate environments. Separate Supabase projects for staging and production.

### 6.3 Railway Deployment Configuration

#### INF-DEVOPS-005: Railway Service Configuration

| Service | Build | Start Command | Resources (MVP) | Health Check |
|---|---|---|---|---|
| `trendedge-api` | Nixpacks (auto-detect Python) | `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --workers 2 --timeout 120` | 512MB RAM, 0.5 vCPU | `GET /health` |
| `trendedge-worker` | Nixpacks | `celery -A app.tasks.celery_app worker --loglevel=info -Q high,default,low,notifications -c 4` | 512MB RAM, 0.5 vCPU | Celery inspect ping |
| `trendedge-beat` | Nixpacks | `celery -A app.tasks.celery_app beat --loglevel=info` | 256MB RAM, 0.25 vCPU | Process alive check |

**Railway configuration (`railway.toml`):**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --workers 2 --timeout 120"
healthcheckPath = "/health"
healthcheckTimeout = 10
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
```

### 6.4 Vercel Deployment Configuration

#### INF-DEVOPS-006: Vercel Configuration

```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "pnpm build",
  "installCommand": "pnpm install --frozen-lockfile",
  "outputDirectory": ".next",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@trendedge-api-url",
    "NEXT_PUBLIC_SUPABASE_URL": "@supabase-url",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase-anon-key",
    "NEXT_PUBLIC_WS_URL": "@trendedge-ws-url"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" }
      ]
    }
  ]
}
```

**Vercel deployment flow:**
1. Push to any branch creates a Preview Deployment (unique URL)
2. Merge to `main` promotes to Production Deployment
3. Environment variables managed via Vercel dashboard (linked to Git branch)

### 6.5 Database Migration Workflow

#### INF-DEVOPS-007: Migration Workflow

```
Developer creates migration locally
    |
    v
alembic revision --autogenerate -m "add_column_x"
    |
    v
Review generated migration (verify up + down)
    |
    v
Test locally: alembic upgrade head && alembic downgrade -1 && alembic upgrade head
    |
    v
Commit migration file + model changes in same PR
    |
    v
CI runs migrations against test database (ephemeral)
    |
    v
Merge to main
    |
    v
CD runs: alembic upgrade head (staging)
    |
    v
Verify staging is healthy
    |
    v
CD runs: alembic upgrade head (production) -- with approval gate in Phase 2+
```

**Migration safety rules:**
1. Never use `DROP TABLE` or `DROP COLUMN` without a prior deprecation migration that adds a replacement.
2. All `ALTER TABLE` operations must be backward-compatible (add nullable columns, not rename).
3. Large data migrations must run as background tasks, not in the Alembic migration itself.
4. Each migration file must complete in under 30 seconds on production data.

### 6.6 Secret Management

#### INF-DEVOPS-008: Secrets Strategy

| Secret Category | Storage Location | Rotation Policy |
|---|---|---|
| Database credentials | Supabase dashboard + Railway env vars | On compromise only (managed by Supabase) |
| Redis URL | Upstash dashboard + Railway env vars | On compromise only |
| Supabase service role key | Supabase dashboard + Railway env vars | On compromise only |
| Supabase JWT secret | Supabase dashboard + Railway env vars | On compromise only |
| Broker API keys | Railway env vars (encrypted) | Every 90 days or on compromise |
| Sentry DSN | Railway env vars | On compromise only |
| Telegram bot token | Railway env vars | On compromise only |
| GitHub Actions secrets | GitHub repository settings | On compromise only |
| Vercel env vars | Vercel dashboard | On compromise only |

**Rules:**
1. `.env` files MUST be in `.gitignore`. The repository MUST contain only `.env.example` with placeholder values.
2. No secret may appear in logs, error messages, or API responses.
3. All secrets in CI/CD pipelines MUST use GitHub Actions encrypted secrets or environment-level secrets.
4. Broker credentials MUST be encrypted at rest in the database using `pgcrypto` or application-level AES-256 encryption.

### 6.7 Monitoring & Alerting

#### INF-DEVOPS-009: Monitoring Stack

| Tool | Purpose | Tier | Cost (MVP) |
|---|---|---|---|
| **Sentry** | Error tracking, performance monitoring | Free (5K events/mo) | $0 |
| **Axiom** | Log aggregation, search, dashboards | Free (500MB/mo ingest) | $0 |
| **Uptime Robot** | Endpoint uptime monitoring, status page | Free (50 monitors, 5-min interval) | $0 |
| **Railway Metrics** | CPU, memory, network, disk per service | Included | $0 |
| **Supabase Dashboard** | Database metrics, query performance | Included | $0 |

#### INF-DEVOPS-010: Alert Configuration

| Alert | Condition | Channel | Severity |
|---|---|---|---|
| API down | `/health/ready` returns non-200 for 2 checks | Telegram + Email | Critical |
| Worker down | Celery inspect ping fails for 5 minutes | Telegram | Critical |
| High error rate | >10 5xx errors in 5 minutes | Sentry + Telegram | High |
| Broker API failure | 3+ consecutive broker call failures | Telegram | Critical |
| Database connection exhaustion | Active connections > 80% of pool | Telegram | High |
| Memory usage | >85% of allocated memory | Telegram | Warning |
| Task queue backlog | >50 pending tasks for >5 minutes | Telegram | Warning |
| Certificate expiry | SSL cert expires in <14 days | Email | Warning |
| Webhook processing slow | p95 > 10 seconds for 10 minutes | Telegram | Warning |

---

## 7. Security Requirements

### 7.1 Authentication

#### INF-SEC-001: API Authentication Architecture

```
Client (Browser)
    |
    | Login via Supabase Auth (email/password, OAuth, magic link)
    |
    v
Supabase Auth
    |
    | Issues JWT (access token + refresh token)
    |
    v
Client stores JWT (httpOnly cookie or localStorage)
    |
    | Sends JWT in Authorization: Bearer <token>
    |
    v
FastAPI
    |
    | Middleware validates JWT:
    |   1. Verify signature (SUPABASE_JWT_SECRET)
    |   2. Check expiration
    |   3. Extract user_id, email, role from claims
    |   4. Attach to request state
    |
    v
Protected Endpoint Handler
```

**JWT Configuration:**

| Parameter | Value |
|---|---|
| Algorithm | HS256 (Supabase default) |
| Access token TTL | 1 hour |
| Refresh token TTL | 7 days |
| Token refresh | Client-side via Supabase SDK `onAuthStateChange` |

#### INF-SEC-002: Webhook Authentication

TradingView webhooks and other inbound webhooks use a separate authentication mechanism:

| Method | Mechanism | Validation |
|---|---|---|
| API Key | Unique key per user, included in webhook payload | Constant-time comparison against stored hash |
| HMAC Signature | `X-Signature` header = HMAC-SHA256(body, secret) | Verify signature integrity |
| IP Allowlist (optional) | TradingView IP ranges | Supplementary, not primary (TradingView IPs change) |

#### INF-SEC-003: Service-to-Service Authentication

| Communication | Auth Method |
|---|---|
| API to Supabase DB | Service role key (connection string) |
| API to Redis | URL with password (TLS) |
| Worker to DB | Same as API (shared service role key) |
| Worker to Redis | Same as API (shared Redis URL) |
| Frontend to API | User JWT (passed through) |
| Frontend to Supabase | Supabase anon key + user JWT (RLS enforced) |

### 7.2 Rate Limiting

#### INF-SEC-004: Rate Limiting Configuration

| Endpoint Category | Rate Limit | Window | Key | Response |
|---|---|---|---|---|
| Authentication (`/auth/*`) | 10 requests | 1 minute | IP | 429 + `Retry-After` header |
| Webhook ingestion (`/webhooks/*`) | 30 requests | 1 minute | API Key | 429 + log alert |
| Read endpoints (`GET /api/v1/*`) | 200 requests | 1 minute | User ID | 429 + `Retry-After` header |
| Write endpoints (`POST/PUT/DELETE /api/v1/*`) | 60 requests | 1 minute | User ID | 429 + `Retry-After` header |
| Analytics (heavy queries) | 20 requests | 1 minute | User ID | 429 + `Retry-After` header |
| WebSocket connections | 10 connections | Per user | User ID | Connection rejected |
| Health checks | Unlimited | N/A | N/A | No rate limiting |

**Implementation:** Redis-based sliding window counter using Upstash Redis. Rate limit state stored with key pattern `ratelimit:{category}:{identifier}` and TTL matching the window duration.

**Response headers on all rate-limited endpoints:**

```
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 150
X-RateLimit-Reset: 1707650400
```

### 7.3 Input Validation

#### INF-SEC-005: Input Validation Framework

| Layer | Tool | Purpose |
|---|---|---|
| API request validation | Pydantic v2 models | Type checking, field constraints, custom validators |
| Database input | SQLAlchemy ORM (parameterized queries) | SQL injection prevention |
| File uploads | Content-type validation + size limits | Prevent malicious file uploads |
| WebSocket messages | Pydantic models | Validate incoming WebSocket messages |
| Webhook payloads | Pydantic models + HMAC verification | Validate and authenticate webhooks |

**Validation rules:**
1. All string inputs MUST have a maximum length (default: 10,000 characters).
2. All numeric inputs MUST have min/max bounds appropriate to the field.
3. All enum fields MUST validate against allowed values.
4. Deeply nested JSON MUST have a maximum depth of 5 levels.
5. File uploads MUST be limited to 10MB (chart screenshots) and validated file types (PNG, JPG, WEBP).
6. All user-facing text outputs MUST be HTML-escaped when rendered.

### 7.4 SQL Injection Prevention

#### INF-SEC-006: Database Security

| Control | Implementation |
|---|---|
| ORM-only queries | All queries through SQLAlchemy ORM. No raw SQL in application code. |
| Parameterized queries | Any exception requiring raw SQL MUST use `text()` with bound parameters. |
| Read replicas | Read-only database user for analytics queries (Phase 2). |
| Row-Level Security | Supabase RLS policies enforce tenant isolation (Phase 3). |
| Connection encryption | `sslmode=require` on all database connections. |

### 7.5 HTTPS Enforcement

#### INF-SEC-007: Transport Security

| Requirement | Implementation |
|---|---|
| All API traffic over HTTPS | Railway provides automatic SSL. HSTS header on all responses. |
| All frontend traffic over HTTPS | Vercel provides automatic SSL. HTTP redirects to HTTPS. |
| Database connections encrypted | Supabase enforces SSL. Connection string includes `sslmode=require`. |
| Redis connections encrypted | Upstash uses `rediss://` (TLS). Plaintext `redis://` connections rejected. |
| WebSocket connections over WSS | Enforced by browser when page is served over HTTPS. |
| Minimum TLS version | TLS 1.2 (enforced by hosting platforms). |

**Security headers (applied by Vercel and FastAPI middleware):**

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0  (deprecated, rely on CSP)
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### 7.6 Secrets Rotation

#### INF-SEC-008: Rotation Policy

| Secret Type | Rotation Frequency | Rotation Method |
|---|---|---|
| Broker API keys | Every 90 days | Manual: regenerate in broker portal, update Railway env vars |
| Supabase service role key | On compromise only | Regenerate in Supabase dashboard |
| Database password | On compromise only | Rotate via Supabase dashboard |
| Redis password | On compromise only | Rotate via Upstash dashboard |
| JWT signing secret | On compromise only | Rotate in Supabase dashboard (invalidates all sessions) |
| Telegram bot token | On compromise only | Regenerate via BotFather |
| User webhook API keys | User-initiated or every 180 days | Self-service via dashboard + API |

### 7.7 OWASP Top 10 Compliance

#### INF-SEC-009: OWASP Coverage

| OWASP Category | Mitigation | Status |
|---|---|---|
| A01: Broken Access Control | Supabase RLS, JWT validation on every request, role-based permissions | Addressed |
| A02: Cryptographic Failures | TLS everywhere, secrets encrypted at rest, no sensitive data in logs | Addressed |
| A03: Injection | ORM-only queries, Pydantic input validation, parameterized queries | Addressed |
| A04: Insecure Design | Threat modeling per feature PRD, principle of least privilege | Addressed |
| A05: Security Misconfiguration | Environment-specific configs, no default credentials, security headers | Addressed |
| A06: Vulnerable Components | Dependabot alerts, monthly dependency audit, pinned versions | Addressed |
| A07: Authentication Failures | Supabase Auth (battle-tested), rate limiting on auth endpoints, MFA support | Addressed |
| A08: Software and Data Integrity | Signed commits, CI/CD pipeline integrity, webhook HMAC verification | Addressed |
| A09: Logging and Monitoring | Structured logging to Axiom, Sentry error tracking, Uptime Robot alerts | Addressed |
| A10: Server-Side Request Forgery | No user-controlled URLs in server requests, allowlist for outbound calls | Addressed |

---

## 8. Dependencies

### 8.1 External Services

| Service | Purpose | Free Tier Limits | Paid Tier Trigger | Criticality |
|---|---|---|---|---|
| **Supabase** | Database, Auth, Storage | 500MB DB, 1GB storage, 50K auth users | >500MB DB or need PITR backups | Critical |
| **Railway** | Backend hosting | $5/mo + usage credits | Always paid (usage-based) | Critical |
| **Vercel** | Frontend hosting | 100GB bandwidth, 100 deploys/day | >100GB bandwidth or team features | Critical |
| **Upstash Redis** | Cache, broker, pub/sub | 10K commands/day, 256MB | >10K cmds/day | Critical |
| **GitHub** | Source control, CI/CD | Unlimited public, 2K Actions min/mo | >2K CI minutes/month | Critical |
| **Sentry** | Error monitoring | 5K events/month | >5K errors/month | High |
| **Axiom** | Log aggregation | 500MB ingest/month, 30-day retention | >500MB logs/month | Medium |
| **Uptime Robot** | Health monitoring | 50 monitors, 5-min interval | Need 1-min interval | Medium |
| **Cloudflare** | DNS, CDN (optional) | Unlimited DNS queries | Need WAF or Workers | Low |

### 8.2 Python Dependencies (Backend)

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | >=0.110 | Web framework |
| `uvicorn[standard]` | >=0.27 | ASGI server |
| `gunicorn` | >=21.2 | Process manager for uvicorn workers |
| `pydantic` | >=2.6 | Data validation |
| `pydantic-settings` | >=2.1 | Environment configuration |
| `sqlalchemy[asyncio]` | >=2.0 | ORM + async engine |
| `asyncpg` | >=0.29 | Async PostgreSQL driver |
| `alembic` | >=1.13 | Database migrations |
| `celery[redis]` | >=5.3 | Task queue |
| `redis` | >=5.0 | Redis client |
| `httpx` | >=0.27 | Async HTTP client (broker APIs, webhooks) |
| `websockets` | >=12.0 | WebSocket support |
| `python-jose[cryptography]` | >=3.3 | JWT decoding and verification |
| `sentry-sdk[fastapi]` | >=1.40 | Error reporting |
| `structlog` | >=24.1 | Structured logging |
| `ruff` | >=0.3 | Linting + formatting (dev) |
| `mypy` | >=1.8 | Type checking (dev) |
| `pytest` | >=8.0 | Testing (dev) |
| `pytest-asyncio` | >=0.23 | Async test support (dev) |
| `pytest-cov` | >=4.1 | Coverage reporting (dev) |
| `httpx` | >=0.27 | Test client (dev) |
| `factory-boy` | >=3.3 | Test data factories (dev) |

### 8.3 Frontend Dependencies

| Package | Version | Purpose |
|---|---|---|
| `next` | >=14.2 | React framework |
| `react` | >=18.2 | UI library |
| `typescript` | >=5.3 | Type safety |
| `tailwindcss` | >=3.4 | Utility CSS |
| `@supabase/supabase-js` | >=2.39 | Supabase client (auth, DB, storage) |
| `@supabase/ssr` | >=0.1 | Supabase server-side auth for Next.js |
| `lightweight-charts` | >=4.1 | TradingView charting library |
| `d3` | >=7.8 | Data visualization |
| `recharts` | >=2.12 | Dashboard charts |
| `shadcn/ui` | latest | UI component library |
| `zustand` | >=4.5 | Client state management |
| `swr` or `@tanstack/react-query` | latest | Server state / data fetching |
| `zod` | >=3.22 | Schema validation (forms) |
| `eslint` | >=8.56 | Linting (dev) |
| `prettier` | >=3.2 | Formatting (dev) |
| `vitest` | >=1.2 | Testing (dev) |

### 8.4 SDK and API Dependencies

| Dependency | Version | Purpose | PRD Reference |
|---|---|---|---|
| `ib_async` | >=1.0 | Interactive Brokers API | PRD-004 |
| `python-telegram-bot` | >=20.7 | Telegram notifications | PRD-008 |
| `anthropic` | >=0.18 | Claude API (AI features) | PRD-009 |
| `scipy` | >=1.12 | Signal processing (trendlines) | PRD-003 |
| `numpy` | >=1.26 | Numerical computing | PRD-003 |
| `pandas` | >=2.2 | Data manipulation | PRD-003 |

---

## 9. Testing Requirements

### 9.1 Unit Testing

#### INF-TEST-001: Unit Testing Framework

| Aspect | Decision |
|---|---|
| Framework | `pytest` with `pytest-asyncio` for async tests |
| Coverage target | 80% line coverage for `app/` (enforced in CI) |
| Coverage exclusions | `alembic/`, `tests/`, `__init__.py`, type stubs |
| Mocking | `unittest.mock` + `pytest-mock` for dependencies |
| Fixtures | Shared fixtures in `tests/conftest.py` |
| Test data | `factory-boy` for model factories, `faker` for realistic data |
| Naming convention | `test_{module}_{function}_{scenario}` (e.g., `test_webhook_validate_valid_signature`) |

**Required unit test coverage areas:**

| Area | What to Test |
|---|---|
| Pydantic models | Validation passes/fails for all fields, edge cases |
| Service layer | Business logic with mocked repositories |
| Security | JWT validation, API key verification, rate limiting logic |
| Utilities | Symbol mapping, time zone conversions, R-multiple calculations |
| Error handlers | Custom exception classes produce correct HTTP responses |

### 9.2 Integration Testing

#### INF-TEST-002: Integration Testing Strategy

| Test Category | Dependencies | Setup |
|---|---|---|
| Database integration | PostgreSQL (Docker) | Ephemeral test DB, migrations applied, rolled back per test |
| Redis integration | Redis (Docker) | Ephemeral Redis, flushed between tests |
| API integration | FastAPI TestClient + DB + Redis | Full request/response cycle against real deps |
| Celery task integration | Celery (eager mode) + DB | Tasks executed synchronously in test process |
| WebSocket integration | FastAPI WebSocket TestClient | Connection, message send/receive, auth |

**Test database strategy:**
1. CI spins up PostgreSQL 16 and Redis 7 as GitHub Actions services.
2. Alembic runs all migrations against the test database.
3. Each test uses a transaction that is rolled back after the test (pytest fixture).
4. No shared state between tests.

### 9.3 Load Testing

#### INF-TEST-003: Load Testing Plan

| Scenario | Tool | Target | Phase |
|---|---|---|---|
| API endpoint throughput | `locust` or `k6` | 100 req/s sustained for 5 minutes | Phase 1 |
| Webhook burst | `k6` | 30 webhooks in 10 seconds (no drops) | Phase 1 |
| WebSocket connections | `k6` or `artillery` | 100 concurrent connections | Phase 2 |
| Database query performance | `pgbench` + custom queries | p95 < 100ms under load | Phase 2 |
| Full pipeline | Custom script | Webhook -> order -> journal in <10s under load | Phase 2 |

**Load test execution:**
- Run against staging environment (never production).
- Scheduled monthly or before major releases.
- Results stored in repository (`tests/load/results/`).

### 9.4 Infrastructure Testing

#### INF-TEST-004: Infrastructure Validation

| Test | What | How | Frequency |
|---|---|---|---|
| Migration reversibility | All migrations can `upgrade` and `downgrade` | CI: `alembic upgrade head && alembic downgrade base && alembic upgrade head` | Every PR with migrations |
| Environment parity | Staging config matches production structure | Script that compares env var keys (not values) | Weekly (CI cron) |
| Health endpoint validity | All health checks return correct status | CI: `curl` against deployed services | Every deploy |
| Secret presence | All required secrets are set | Script that checks non-empty env vars | Every deploy |
| Docker build | Dockerfile builds successfully | CI: `docker build .` | Every PR |

### 9.5 CI Pipeline Test Stages

#### INF-TEST-005: Test Stage Ordering

```
Stage 1: Static Analysis (fastest, fail fast)
    - Ruff lint
    - Ruff format check
    - mypy type check
    - ESLint (frontend)
    - TypeScript check (frontend)
    Duration target: <60 seconds

Stage 2: Unit Tests
    - pytest (unit tests only, no DB/Redis)
    - vitest (frontend unit tests)
    Duration target: <120 seconds

Stage 3: Integration Tests
    - pytest (integration tests with Docker services)
    Duration target: <300 seconds

Stage 4: Build Verification
    - Docker build (backend)
    - Next.js build (frontend)
    Duration target: <180 seconds

Total CI target: <10 minutes
```

---

## 10. Acceptance Criteria

### 10.1 Infrastructure Readiness Checklist

The infrastructure is considered ready for feature development when ALL of the following criteria are met:

#### Backend (FastAPI)

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-001 | FastAPI application starts and responds to requests on `/health` | `curl http://localhost:8000/health` returns 200 |
| INF-AC-002 | All middleware is active (CORS, logging, timing, error handling) | Request to any endpoint includes `X-Request-ID` header and is logged |
| INF-AC-003 | API versioning works (`/api/v1/` prefix routing) | Endpoints respond under `/api/v1/` |
| INF-AC-004 | Error responses follow the standard JSON structure | Intentional 400/404/500 errors return correct format |
| INF-AC-005 | OpenAPI docs are generated and accessible | `/docs` (Swagger UI) and `/openapi.json` are accessible in dev/staging |

#### Database

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-006 | SQLAlchemy async engine connects to Supabase via Supavisor | Application logs show successful DB connection on startup |
| INF-AC-007 | Alembic migrations run forward and backward cleanly | `alembic upgrade head && alembic downgrade base && alembic upgrade head` succeeds |
| INF-AC-008 | At least one model + migration exists (e.g., `users` table) | `SELECT * FROM users` succeeds |
| INF-AC-009 | Connection pooling is configured and respects limits | Pool size is 10, max overflow is 5, `statement_cache_size=0` |

#### Redis

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-010 | Redis client connects to Upstash over TLS | Application logs show successful Redis connection |
| INF-AC-011 | Cache set/get operations work | Health check verifies Redis PING returns PONG |
| INF-AC-012 | Rate limiting middleware functions correctly | Exceeding rate limit returns 429 with correct headers |

#### Celery

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-013 | Celery worker starts and connects to Redis broker | Worker log shows "celery@hostname ready" |
| INF-AC-014 | A test task can be dispatched and completed | `test_task.delay()` returns a result within 5 seconds |
| INF-AC-015 | Celery Beat starts and schedules a periodic task | Beat log shows scheduled task registration |

#### WebSocket

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-016 | WebSocket endpoint accepts authenticated connections | Client connects to `/api/v1/ws` with valid JWT |
| INF-AC-017 | Events published to Redis are delivered to WebSocket clients | Publish a test event, verify client receives it within 1 second |

#### Authentication

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-018 | Supabase Auth JWT validation works | Request with valid JWT returns 200; invalid JWT returns 401 |
| INF-AC-019 | Protected endpoints reject unauthenticated requests | Request without `Authorization` header returns 401 |

#### DevOps

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-020 | `docker compose up` starts full local stack (API, worker, DB, Redis) | All services healthy within 60 seconds |
| INF-AC-021 | CI pipeline runs lint, type check, and tests on push | GitHub Actions workflow passes on a clean commit |
| INF-AC-022 | CD pipeline deploys to Railway on merge to `main` | Merge triggers deployment; health check passes after deploy |
| INF-AC-023 | Frontend deploys to Vercel on push | Vercel preview deployment is created for PR; production on merge |
| INF-AC-024 | All required environment variables are documented in `.env.example` | `.env.example` contains every key referenced in `config.py` |

#### Monitoring

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-025 | Errors are reported to Sentry with context | Trigger a test error; verify it appears in Sentry within 60 seconds |
| INF-AC-026 | Logs are forwarded to Axiom | Application logs appear in Axiom dashboard within 5 minutes |
| INF-AC-027 | Uptime Robot monitors `/health/ready` | Monitor is active; test downtime triggers alert |
| INF-AC-028 | Structured JSON logs include `request_id`, `method`, `path`, `status_code`, `duration_ms` | Inspect log output for a test request |

#### Security

| ID | Criterion | Verification |
|---|---|---|
| INF-AC-029 | All API traffic is encrypted (HTTPS/WSS) | `curl http://` redirects to `https://`; SSL Labs test scores A+ |
| INF-AC-030 | Security headers are present on all responses | Verify `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options` headers |
| INF-AC-031 | No secrets in source code or logs | `git log -p | grep -i "password\|secret\|api_key"` returns no real secrets |

---

## 11. Phase Mapping

### Phase 1: Personal Trading System (Weeks 1-8)

**Infrastructure scope:** Everything needed for a single-user system with paper trading.

| Requirement | ID | Week | Notes |
|---|---|---|---|
| FastAPI scaffold + project structure | INF-FR-001 | 1 | Full structure, minimal endpoints |
| Middleware stack (CORS, logging, errors) | INF-FR-002, 003 | 1 | All middleware from day 1 |
| Supabase PostgreSQL setup + Alembic | INF-FR-004, 005 | 1 | Connection pooling, first migration |
| Upstash Redis setup | INF-FR-007, 008 | 1 | Cache + Celery broker |
| Celery worker + beat setup | INF-FR-009, 010, 011 | 1-2 | Single worker, all queues |
| Health check endpoints | INF-FR-015 | 1 | Liveness + readiness |
| Environment config (Pydantic Settings) | INF-FR-013, 014 | 1 | Dev + prod only |
| Supabase Auth + JWT validation | INF-SEC-001 | 1-2 | Basic auth flow |
| Docker Compose (local dev) | INF-US-001 | 1 | Full local stack |
| GitHub Actions CI (lint + test) | INF-DEVOPS-002 | 2 | Automated on push |
| Railway deployment (API + worker) | INF-DEVOPS-005 | 2 | Manual deploy initially, then CD |
| Vercel deployment (frontend) | INF-DEVOPS-006 | 7 | When frontend work begins |
| Sentry integration | INF-DEVOPS-009 | 2 | Error tracking from day 1 |
| Uptime Robot monitoring | INF-DEVOPS-010 | 2 | Health check monitoring |
| WebSocket support (basic) | INF-FR-012 | 7-8 | When dashboard is built |
| Webhook endpoint (TradingView) | INF-SEC-002 | 2 | Authentication + dedup |
| Rate limiting (basic) | INF-SEC-004 | 2 | Auth + webhook endpoints |
| Request/response logging | INF-FR-018 | 1 | Structured JSON from day 1 |
| API versioning | INF-FR-016 | 1 | `/api/v1/` prefix |
| Database backup (pg_dump cron) | INF-FR-006 | 3 | Nightly backup to storage |
| Input validation framework | INF-SEC-005 | 1 | Pydantic on all endpoints |

### Phase 2: Analytics & Journaling (Weeks 9-14)

**Infrastructure additions:** Performance optimization, staging environment, enhanced monitoring.

| Requirement | ID | Week | Notes |
|---|---|---|---|
| Staging environment | INF-DEVOPS-004 | 9 | Separate Supabase project |
| CD pipeline with staging gate | INF-DEVOPS-003 | 9 | Auto-deploy staging, manual prod |
| Axiom log aggregation | INF-DEVOPS-009 | 9 | Railway log drain |
| Database query optimization | INF-NFR-007 | 10 | Indexes for analytics queries |
| Load testing (initial) | INF-TEST-003 | 13 | API + webhook throughput |
| Redis caching for analytics | INF-FR-007 | 11 | Cache heavy aggregations |
| File storage (screenshots) | INF-SEC-005 | 10 | Supabase Storage or R2 |
| WebSocket enhancements | INF-FR-012 | 11 | Full event catalog |
| Integration test suite | INF-TEST-002 | 9-10 | DB + Redis integration tests |

### Phase 3: Multi-Tenant SaaS (Weeks 15-22)

**Infrastructure additions:** Multi-tenancy, scaling, production hardening.

| Requirement | ID | Week | Notes |
|---|---|---|---|
| Row-Level Security (Supabase RLS) | INF-SEC-006 | 15 | Tenant isolation in database |
| Supabase Pro upgrade (PITR backups) | INF-FR-006 | 15 | Point-in-time recovery |
| Horizontal worker scaling | INF-NFR-017 | 17 | 2-3 worker instances |
| Production approval gate in CD | INF-DEVOPS-003 | 15 | GitHub environment protection |
| Secrets rotation automation | INF-SEC-008 | 16 | 90-day broker key rotation |
| Load testing (full pipeline) | INF-TEST-003 | 20 | End-to-end under load |
| Disaster recovery drill | INF-FR-006 | 21 | Restore from backup test |
| Security audit | INF-SEC-009 | 19 | OWASP Top 10 review |
| Dependabot + dependency audit | INF-SEC-009 | 15 | Automated vulnerability scanning |
| Upscale Railway resources | INF-DEVOPS-005 | 17 | 1GB RAM, 1 vCPU per service |

### Cost Progression by Phase

| Phase | Monthly Cost | Key Upgrades |
|---|---|---|
| Phase 1 (Weeks 1-8) | $30-60 | Railway usage, free tiers everywhere else |
| Phase 2 (Weeks 9-14) | $50-90 | Slight increase in Railway usage, still free tiers |
| Phase 3 (Weeks 15-22) | $80-150 | Supabase Pro ($25), more Railway compute, Upstash paid |
| Post-Launch (100+ users) | $250-500 | Scaled Railway, Supabase Pro, Upstash Pro |

---

## 12. Cross-References to Other PRDs

| PRD | Title | Infrastructure Dependency | Provides to This PRD |
|---|---|---|---|
| **PRD-002** | Data Models & Database Schema | Database setup (INF-FR-004, 005), Alembic migrations, Supabase RLS | Schema definitions, model relationships, index strategy |
| **PRD-003** | Trendline Detection Engine | Celery workers (INF-FR-009), task retry policies (INF-FR-011) | Compute requirements, task scheduling needs |
| **PRD-004** | Broker Adapters | Environment config (INF-FR-013), secret management (INF-DEVOPS-008), circuit breaker (INF-FR-011) | Broker credential requirements, connection lifecycle |
| **PRD-005** | Trade Execution Pipeline | Webhook endpoint (INF-SEC-002), WebSocket (INF-FR-012), Redis pub/sub (INF-FR-007) | Latency requirements (INF-NFR-001), idempotency needs |
| **PRD-006** | Journaling & Playbooks | File storage (Supabase Storage), database transactions (INF-NFR-021) | Storage requirements, upload size limits |
| **PRD-007** | Dashboard UI | Vercel deployment (INF-DEVOPS-006), WebSocket client, CORS (INF-FR-017), API versioning (INF-FR-016) | Frontend hosting needs, real-time update requirements |
| **PRD-008** | Notifications | Celery notification queue (INF-FR-009), Telegram bot config (INF-FR-013) | Notification delivery SLA, channel configuration |
| **PRD-009** | AI/ML Features | Celery low-priority queue (INF-FR-009), Claude API credentials (INF-DEVOPS-008) | Compute requirements, API cost projections |
| **PRD-010** | Billing & Subscriptions | Supabase Auth integration (INF-SEC-001), environment config (INF-FR-013) | Stripe webhook requirements, subscription tier data |
| **PRD-011** | Analytics Engine | Redis caching (INF-FR-007), database query optimization (INF-NFR-007) | Query performance requirements, materialized view strategy |

---

## 13. Appendix

### 13.1 Glossary

| Term | Definition |
|---|---|
| **Supavisor** | Supabase's built-in connection pooler (replaces PgBouncer). Port 6543, transaction mode. |
| **RLS** | Row-Level Security. PostgreSQL feature that restricts row access per-user. Supabase uses it for multi-tenant isolation. |
| **Circuit Breaker** | A pattern that stops calling a failing service after N consecutive failures, resuming after a cooldown period. |
| **Nixpacks** | Railway's build system that auto-detects language and creates optimized container images. |
| **PITR** | Point-in-Time Recovery. Ability to restore a database to any moment using WAL (Write-Ahead Log) archives. |
| **Idempotency** | The property that performing an operation multiple times has the same effect as performing it once. Critical for webhook processing. |
| **MAE/MFE** | Maximum Adverse/Favorable Excursion. Measures the worst and best price movement during a trade's lifetime. |

### 13.2 Decision Log

| Decision | Options Considered | Chosen | Rationale |
|---|---|---|---|
| Primary database | Supabase PostgreSQL, Railway PostgreSQL, PlanetScale | Supabase | Built-in Auth, Storage, RLS, free tier, dashboard |
| Backend hosting | Railway, Render, Fly.io, AWS ECS | Railway | Best DX, persistent processes for broker connections, simple scaling, built-in metrics |
| Frontend hosting | Vercel, Netlify, Cloudflare Pages | Vercel | Native Next.js support, edge functions, preview deployments, free hobby tier |
| Task queue | Celery + Redis, Dramatiq, ARQ, Huey | Celery + Redis | Most mature, best ecosystem, Upstash Redis doubles as cache + broker |
| Redis provider | Upstash, Railway Redis, ElastiCache | Upstash | Serverless (no idle cost), TLS built-in, free tier, REST API fallback |
| Migration tool | Alembic, Supabase Migrations CLI | Alembic | Native SQLAlchemy integration, auto-generation, mature ecosystem |
| Auth provider | Supabase Auth, Clerk, Auth0, NextAuth | Supabase Auth | Already using Supabase, free tier generous, JWT-based, built-in RLS integration |
| Monitoring | Sentry + Axiom + Uptime Robot, Datadog, New Relic | Sentry + Axiom + Uptime Robot | All have free tiers covering MVP needs. Combined cost: $0 for Phase 1. |
| Logging format | Structured JSON, plaintext | Structured JSON | Machine-parseable, Axiom-native, enables log-based alerting |
| API versioning | URL path, header-based, query parameter | URL path (`/api/v1/`) | Most explicit, easiest to route, industry standard |

### 13.3 Local Development Quick Start

```bash
# Clone and setup
git clone https://github.com/trendedge/trendedge.git
cd trendedge

# Copy environment template
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Start all services (PostgreSQL, Redis, API, Worker, Beat)
cd backend && docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Seed test data
docker compose exec api python -m app.scripts.seed

# Start frontend (separate terminal)
cd frontend && pnpm install && pnpm dev

# Verify
curl http://localhost:8000/health/ready
# Expected: {"status":"ok","checks":{...}}

# Open dashboard
open http://localhost:3000
```

### 13.4 Docker Compose (Local Development)

```yaml
# backend/docker-compose.yml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: trendedge
      POSTGRES_PASSWORD: trendedge_dev
      POSTGRES_DB: trendedge
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trendedge"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      uvicorn app.main:app
      --host 0.0.0.0
      --port 8000
      --reload
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://trendedge:trendedge_dev@postgres:5432/trendedge
      UPSTASH_REDIS_URL: redis://redis:6379/0
      APP_ENV: development
      APP_DEBUG: "true"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      celery -A app.tasks.celery_app worker
      --loglevel=debug
      -Q high,default,low,notifications
      -c 2
    volumes:
      - .:/app
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://trendedge:trendedge_dev@postgres:5432/trendedge
      UPSTASH_REDIS_URL: redis://redis:6379/0
      APP_ENV: development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  beat:
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      celery -A app.tasks.celery_app beat
      --loglevel=info
    volumes:
      - .:/app
    env_file:
      - .env
    environment:
      UPSTASH_REDIS_URL: redis://redis:6379/0
      APP_ENV: development
    depends_on:
      redis:
        condition: service_healthy

volumes:
  postgres_data:
```

### 13.5 Disaster Recovery Plan

| Scenario | Detection | Recovery Procedure | RTO | RPO |
|---|---|---|---|---|
| **API server crash** | Uptime Robot alert (2 min) | Railway auto-restart (ON_FAILURE policy). If persistent: redeploy from last known-good commit. | 5 min | 0 (stateless) |
| **Database corruption** | Application errors + Sentry | Restore from Supabase backup (daily) or PITR (Phase 3). | 30-60 min | 24h (Free) / minutes (Pro) |
| **Redis failure** | Health check fails, Celery stalls | Upstash auto-recovery. If prolonged: API falls back to sync processing for critical tasks. | 5 min | 0 (cache, rebuildable) |
| **Celery worker crash** | Tasks stop processing, queue grows | Railway auto-restart. Unfinished tasks redelivered (acks_late). | 5 min | 0 (tasks redelivered) |
| **Supabase outage** | Health check returns 503 | Wait for Supabase recovery. No self-hosted fallback. Notify users of degraded mode. | Dependent on Supabase | Dependent on Supabase |
| **Railway outage** | Uptime Robot alert | If >30 min: consider emergency deploy to Render/Fly.io from same Docker image. | 30-60 min | 0 (stateless services) |
| **Secret compromise** | Audit log anomaly, unauthorized access | Rotate all affected secrets. Invalidate sessions. Audit access logs. Notify affected users. | 1-4 hours | N/A |
| **Full data loss** | Cannot connect to any backup | Restore from pg_dump stored in R2/Supabase Storage (30-day retention). | 2-4 hours | 24 hours |

**Recovery priority order:**
1. Database (data is irreplaceable)
2. API server (user-facing)
3. Celery workers (async processing)
4. Celery Beat (periodic tasks)
5. Frontend (Vercel has independent uptime)

---

*End of PRD-001: Platform Infrastructure & DevOps*

*This document should be reviewed and updated quarterly or when significant architectural decisions change. All changes must be tracked in the Decision Log (Appendix 13.2).*
