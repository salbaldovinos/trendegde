"""Health check endpoints for liveness, readiness, and diagnostics."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("trendedge.health")

router = APIRouter(tags=["health"])

# Track startup time for uptime calculation
_start_time: float = time.time()


def set_start_time() -> None:
    """Set the application start time (called during startup)."""
    global _start_time  # noqa: PLW0603
    _start_time = time.time()


@router.get("/health")
async def liveness() -> dict:
    """Liveness probe -- always returns 200 if the process is running."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@router.get("/health/ready")
async def readiness(request: Request) -> JSONResponse:
    """Readiness probe -- checks database, Redis, and Celery."""
    checks: dict[str, dict] = {}
    all_ok = True

    async def check_db() -> None:
        nonlocal all_ok
        start = time.perf_counter()
        try:
            engine = getattr(request.app.state, "db_engine", None)
            if engine is None:
                checks["database"] = {"status": "error", "error": "Engine not initialized"}
                all_ok = False
                return
            from sqlalchemy import text

            async with engine.connect() as conn:
                await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=5.0)
            latency = round((time.perf_counter() - start) * 1000, 2)
            checks["database"] = {"status": "ok", "latency_ms": latency}
        except Exception as exc:
            latency = round((time.perf_counter() - start) * 1000, 2)
            checks["database"] = {"status": "error", "latency_ms": latency, "error": str(exc)}
            all_ok = False

    async def check_redis() -> None:
        nonlocal all_ok
        start = time.perf_counter()
        try:
            redis = getattr(request.app.state, "redis", None)
            redis_available = getattr(request.app.state, "redis_available", False)
            if not redis or not redis_available:
                checks["redis"] = {"status": "error", "error": "Redis not available"}
                all_ok = False
                return
            await asyncio.wait_for(redis.ping(), timeout=5.0)
            latency = round((time.perf_counter() - start) * 1000, 2)
            checks["redis"] = {"status": "ok", "latency_ms": latency}
        except Exception as exc:
            latency = round((time.perf_counter() - start) * 1000, 2)
            checks["redis"] = {"status": "error", "latency_ms": latency, "error": str(exc)}
            all_ok = False

    async def check_celery() -> None:
        nonlocal all_ok
        start = time.perf_counter()
        try:
            from celery import Celery

            celery_app: Celery | None = getattr(request.app.state, "celery_app", None)
            if celery_app is None:
                checks["celery"] = {"status": "error", "error": "Celery not configured"}
                all_ok = False
                return

            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: celery_app.control.ping(timeout=5.0)),
                timeout=10.0,
            )
            latency = round((time.perf_counter() - start) * 1000, 2)
            if result:
                checks["celery"] = {"status": "ok", "latency_ms": latency}
            else:
                checks["celery"] = {"status": "error", "latency_ms": latency, "error": "No workers responded"}
                all_ok = False
        except Exception as exc:
            latency = round((time.perf_counter() - start) * 1000, 2)
            checks["celery"] = {"status": "error", "latency_ms": latency, "error": str(exc)}
            all_ok = False

    await asyncio.gather(check_db(), check_redis(), check_celery())

    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "version": settings.APP_VERSION,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checks": checks,
        },
    )


@router.get("/health/detailed")
async def detailed(request: Request) -> JSONResponse:
    """Diagnostic endpoint -- requires operator API key."""
    api_key = request.headers.get("X-API-Key", "")
    if not settings.OPERATOR_API_KEY or api_key != settings.OPERATOR_API_KEY:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Valid operator API key required.",
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            },
        )

    uptime_seconds = round(time.time() - _start_time, 2)

    # Database pool stats
    db_stats: dict = {}
    engine = getattr(request.app.state, "db_engine", None)
    if engine is not None:
        pool = engine.pool
        db_stats = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }

    # Redis info
    redis_stats: dict = {}
    redis = getattr(request.app.state, "redis", None)
    redis_available = getattr(request.app.state, "redis_available", False)
    if redis and redis_available:
        try:
            info = await redis.info(section="memory")
            redis_stats = {
                "connected": True,
                "used_memory_human": info.get("used_memory_human", "unknown"),
            }
        except Exception:
            redis_stats = {"connected": False}
    else:
        redis_stats = {"connected": False}

    # Celery queue lengths
    celery_stats: dict = {}
    try:
        if redis and redis_available:
            for queue_name in ("high", "default", "low", "notifications"):
                length = await redis.llen(queue_name)
                celery_stats[queue_name] = length
    except Exception:
        celery_stats = {"error": "Unable to fetch queue stats"}

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "database": db_stats,
            "redis": redis_stats,
            "celery_queues": celery_stats,
        },
    )
