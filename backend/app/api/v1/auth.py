"""Authentication route handlers."""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, RateLimitError
from app.core.rate_limit import check_rate_limit
from app.core.security import get_current_user
from app.db.session import get_db
from app.core.redis import get_redis
from app.schemas.requests.auth import (
    LoginRequest,
    MagicLinkRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordUpdateRequest,
    RefreshRequest,
    ResendVerificationRequest,
    SignupRequest,
    VerifyOtpRequest,
)
from app.schemas.responses.auth import AuthResponse, MessageResponse, OAuthUrlResponse
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


# ------------------------------------------------------------------
# POST /auth/magic-link
# ------------------------------------------------------------------

@router.post("/magic-link", response_model=MessageResponse)
async def magic_link(
    body: MagicLinkRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Send a magic link (passwordless login) email."""
    ip = _get_ip(request)
    email_hash = _hash_email(body.email)

    # Rate limit: 3 per email per 15 minutes
    rl = await check_rate_limit(
        redis, f"ratelimit:email:{email_hash}:magic_link", max_requests=3, window_seconds=900
    )
    if not rl.allowed:
        raise RateLimitError(retry_after=rl.reset_at)

    svc = AuthService(db, redis)
    await svc.magic_link(body.email, ip, _get_ua(request))
    # Always return the same message regardless of whether the email exists
    return MessageResponse(
        message="Check your email for a login link. The link expires in 1 hour."
    )


# ------------------------------------------------------------------
# POST /auth/verify-otp
# ------------------------------------------------------------------

@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(
    body: VerifyOtpRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    """Verify a magic link or signup OTP token."""
    svc = AuthService(db, redis)
    result = await svc.verify_otp(
        body.token_hash, body.type, _get_ip(request), _get_ua(request)
    )
    return AuthResponse(**result)


# ------------------------------------------------------------------
# GET /auth/oauth/{provider}
# ------------------------------------------------------------------

@router.get("/oauth/{provider}", response_model=OAuthUrlResponse)
async def oauth_redirect(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OAuthUrlResponse:
    """Get the OAuth authorization URL for the given provider."""
    redirect_to = str(request.query_params.get("redirect_to", ""))
    svc = AuthService(db, redis)
    url = await svc.get_oauth_url(provider, redirect_to)
    return OAuthUrlResponse(url=url, provider=provider)


# ------------------------------------------------------------------
# POST /auth/password/reset
# ------------------------------------------------------------------

@router.post("/password/reset", response_model=MessageResponse)
async def password_reset(
    body: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Request a password reset email."""
    ip = _get_ip(request)
    email_hash = _hash_email(body.email)

    # Rate limit: 3 per email per hour
    rl = await check_rate_limit(
        redis, f"ratelimit:email:{email_hash}:password_reset", max_requests=3, window_seconds=3600
    )
    if not rl.allowed:
        raise RateLimitError(retry_after=rl.reset_at)

    svc = AuthService(db, redis)
    await svc.request_password_reset(body.email, ip, _get_ua(request))
    # Always return the same message regardless of whether the email exists
    return MessageResponse(
        message="If an account exists with that email, you will receive a password reset link."
    )


# ------------------------------------------------------------------
# POST /auth/password/update
# ------------------------------------------------------------------

@router.post("/password/update", response_model=MessageResponse)
async def password_update(
    body: PasswordUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Set a new password using a reset token (access token from reset link)."""
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer" or not parts[1].strip():
        raise AuthenticationError("Authentication required.")
    access_token = parts[1].strip()

    svc = AuthService(db, redis)
    await svc.update_password(access_token, body.new_password, _get_ip(request), _get_ua(request))
    return MessageResponse(message="Password updated successfully.")


# ------------------------------------------------------------------
# POST /auth/password/change (authenticated)
# ------------------------------------------------------------------

@router.post("/password/change", response_model=MessageResponse)
async def password_change(
    body: PasswordChangeRequest,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Change password for authenticated user (requires current password)."""
    access_token = request.headers["Authorization"].split(" ", 1)[1]

    # We need the user's email to verify current password.
    # Get it from Supabase using the access token.
    svc = AuthService(db, redis)
    email = await svc.get_user_email(access_token)

    await svc.change_password(
        email=email,
        current_password=body.current_password,
        new_password=body.new_password,
        access_token=access_token,
        ip=_get_ip(request),
        user_agent=_get_ua(request),
    )
    return MessageResponse(message="Password changed successfully.")


# ------------------------------------------------------------------
# POST /auth/verify/resend (authenticated)
# ------------------------------------------------------------------

@router.post("/verify/resend", response_model=MessageResponse)
async def resend_verification(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    """Resend email verification for the authenticated user."""
    # Rate limit: 3 per hour
    rl = await check_rate_limit(
        redis, f"ratelimit:user:{user_id}:verify_resend", max_requests=3, window_seconds=3600
    )
    if not rl.allowed:
        raise RateLimitError(retry_after=rl.reset_at)

    access_token = request.headers["Authorization"].split(" ", 1)[1]
    svc = AuthService(db, redis)
    email = await svc.get_user_email(access_token)
    await svc.resend_verification(email, _get_ip(request), _get_ua(request))
    return MessageResponse(
        message="Verification email sent. Please check your inbox."
    )
