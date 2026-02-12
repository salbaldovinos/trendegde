"""Authentication route handlers."""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RateLimitError
from app.core.rate_limit import check_rate_limit
from app.core.security import get_current_user
from app.db.session import get_db
from app.core.redis import get_redis
from app.schemas.requests.auth import LoginRequest, RefreshRequest, SignupRequest
from app.schemas.responses.auth import AuthResponse, MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_ip(request: Request) -> str:
    return request.client.host if request.client else "0.0.0.0"


def _get_ua(request: Request) -> str:
    return request.headers.get("user-agent", "")


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.lower().encode()).hexdigest()


# ------------------------------------------------------------------
# POST /auth/signup
# ------------------------------------------------------------------

@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(
    body: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    """Register a new user account."""
    # Rate limit: 5 per IP per hour
    ip = _get_ip(request)
    rl = await check_rate_limit(redis, f"ratelimit:ip:{ip}:signup", max_requests=5, window_seconds=3600)
    if not rl.allowed:
        raise RateLimitError(retry_after=rl.reset_at)

    svc = AuthService(db, redis)
    result = await svc.signup(body.email, body.password, ip, _get_ua(request))
    result["message"] = "Account created successfully."
    return AuthResponse(**result)


# ------------------------------------------------------------------
# POST /auth/login
# ------------------------------------------------------------------

@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    """Authenticate with email and password."""
    ip = _get_ip(request)

    # Rate limit: 10 per IP per minute
    rl_ip = await check_rate_limit(redis, f"ratelimit:ip:{ip}:login", max_requests=10, window_seconds=60)
    if not rl_ip.allowed:
        raise RateLimitError(retry_after=rl_ip.reset_at)

    svc = AuthService(db, redis)
    result = await svc.login(body.email, body.password, ip, _get_ua(request))
    return AuthResponse(**result)


# ------------------------------------------------------------------
# POST /auth/logout
# ------------------------------------------------------------------

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Sign out the authenticated user."""
    token = request.headers["Authorization"].split(" ", 1)[1]
    svc = AuthService(db, redis)
    await svc.logout(token)
    return MessageResponse(message="Successfully logged out.")


# ------------------------------------------------------------------
# POST /auth/refresh
# ------------------------------------------------------------------

@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    """Refresh an expired session using a refresh token."""
    svc = AuthService(db, redis)
    result = await svc.refresh(body.refresh_token)
    return AuthResponse(**result)
