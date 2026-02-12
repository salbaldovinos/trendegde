"""FastAPI application factory with lifespan management."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    TimingMiddleware,
)

logger = get_logger("trendedge.main")

REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "UPSTASH_REDIS_URL",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
]


def _validate_env() -> None:
    """Ensure all required environment variables are set."""
    missing = [var for var in REQUIRED_ENV_VARS if not getattr(settings, var, "")]
    if missing:
        logger.critical("Missing required environment variables", missing=missing)
        sys.exit(1)


async def _init_database(app: FastAPI) -> None:
    """Verify database connectivity with retry using the shared engine."""
    from sqlalchemy import text

    from app.db.session import engine

    for attempt in range(1, 4):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established", attempt=attempt)
            app.state.db_engine = engine
            return
        except Exception as exc:
            logger.warning(
                "Database connection attempt failed",
                attempt=attempt,
                error=str(exc),
            )
            if attempt == 3:
                logger.critical(
                    "Cannot connect to database after 3 attempts. Last error: %s",
                    str(exc),
                )
                sys.exit(1)
            await asyncio.sleep(1)


async def _init_redis(app: FastAPI) -> None:
    """Initialize Redis client with retry. Degrades gracefully on failure."""
    from app.core.redis import init_redis

    redis = init_redis()

    for attempt in range(1, 4):
        try:
            await redis.ping()
            logger.info("Redis connection established", attempt=attempt)
            app.state.redis = redis
            app.state.redis_available = True
            return
        except Exception as exc:
            logger.warning(
                "Redis connection attempt failed",
                attempt=attempt,
                error=str(exc),
            )
            if attempt == 3:
                logger.warning(
                    "Cannot connect to Redis. Starting in degraded mode (no caching, synchronous task processing)."
                )
                app.state.redis = redis
                app.state.redis_available = False
                return
            await asyncio.sleep(1)


def _init_sentry() -> None:
    """Initialize Sentry error tracking if DSN is configured."""
    if not settings.SENTRY_DSN:
        return
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1 if settings.is_production else 1.0,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
    )
    logger.info("Sentry initialized")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown logic."""
    # --- Startup ---
    setup_logging()
    _validate_env()
    await _init_database(app)
    await _init_redis(app)
    _init_sentry()

    from app.api.v1.health import set_start_time

    set_start_time()

    logger.info(
        "TrendEdge API v%s started successfully in %s mode",
        settings.APP_VERSION,
        settings.APP_ENV,
    )

    yield

    # --- Shutdown ---
    logger.info("TrendEdge API shutting down...")

    engine = getattr(app.state, "db_engine", None)
    if engine is not None:
        await engine.dispose()
        logger.info("Database engine disposed")

    redis = getattr(app.state, "redis", None)
    if redis is not None:
        await redis.close()
        logger.info("Redis connection closed")

    logger.info("TrendEdge API shutdown complete.")


def create_app() -> FastAPI:
    """Build and return the FastAPI application instance."""
    app = FastAPI(
        title="TrendEdge API",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # --- Middleware (outermost first → added last) ---
    # Starlette applies middleware in reverse registration order,
    # so we register from innermost to outermost.
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
        expose_headers=["X-Request-ID", "X-API-Version", "X-RateLimit-Remaining"],
        max_age=600,
    )

    # --- API version header on every response ---
    @app.middleware("http")
    async def add_api_version_header(request: Request, call_next: object) -> Response:
        response = await call_next(request)  # type: ignore[misc]
        response.headers["X-API-Version"] = "v1"
        return response  # type: ignore[return-value]

    # --- Routers ---
    from app.api.v1.health import router as health_router
    from app.api.v1.router import router as v1_router

    app.include_router(health_router)
    app.include_router(v1_router)

    # --- Exception handlers ---
    register_exception_handlers(app)

    return app


app = create_app()
