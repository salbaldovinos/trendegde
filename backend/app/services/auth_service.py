"""Business logic for authentication: signup, login, logout, refresh."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, RateLimitError
from app.core.logging import get_logger
from app.core.rate_limit import (
    check_rate_limit,
    increment_failed_login,
    is_account_locked,
    reset_failed_login,
)
from app.db.models.audit_log import AuditLog

logger = get_logger("trendedge.auth_service")

_SUPABASE_HEADERS = {
    "apikey": settings.SUPABASE_ANON_KEY,
    "Content-Type": "application/json",
}
_AUTH_BASE = f"{settings.SUPABASE_URL}/auth/v1"


def _hash_email(email: str) -> str:
    """SHA-256 hash of a lowercased email for safe use in Redis keys."""
    return hashlib.sha256(email.lower().encode()).hexdigest()


class AuthService:
    """Handles all Supabase Auth REST API interactions and audit logging."""

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self._db = db
        self._redis = redis

    # ------------------------------------------------------------------
    # Signup
    # ------------------------------------------------------------------

    async def signup(
        self, email: str, password: str, ip: str, user_agent: str
    ) -> dict:
        """Register a new user via the Supabase Auth REST API."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{_AUTH_BASE}/signup",
                headers=_SUPABASE_HEADERS,
                json={"email": email, "password": password},
            )

        body = resp.json()

        if resp.status_code == 422 or (
            resp.status_code == 400
            and "already registered" in body.get("msg", body.get("message", "")).lower()
        ):
            raise ConflictError("An account with this email already exists.")

        if resp.status_code >= 400:
            logger.warning(
                "Supabase signup error",
                status=resp.status_code,
                email_hash=_hash_email(email),
            )
            raise AuthenticationError(
                body.get("msg", body.get("message", "Signup failed. Please try again."))
            )

        user_id = body.get("id") or body.get("user", {}).get("id")
        await self._audit(
            user_id=user_id,
            event_type="user_registered",
            event_data={"email_hash": _hash_email(email)},
            ip=ip,
            user_agent=user_agent,
        )

        return self._build_auth_response(body)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(
        self, email: str, password: str, ip: str, user_agent: str
    ) -> dict:
        """Authenticate a user via Supabase signInWithPassword."""
        email_hash = _hash_email(email)

        # Check account lock
        locked, retry_after = await is_account_locked(self._redis, email_hash)
        if locked:
            raise RateLimitError(retry_after=retry_after)

        # Per-email rate limit: 10 attempts per 15 min
        rl = await check_rate_limit(
            self._redis,
            f"ratelimit:email:{email_hash}:login",
            max_requests=10,
            window_seconds=900,
        )
        if not rl.allowed:
            raise RateLimitError(retry_after=rl.reset_at)

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{_AUTH_BASE}/token?grant_type=password",
                headers=_SUPABASE_HEADERS,
                json={"email": email, "password": password},
            )

        body = resp.json()

        if resp.status_code >= 400:
            fail_count = await increment_failed_login(self._redis, email_hash, ip)
            await self._audit(
                user_id=None,
                event_type="login_failure",
                event_data={
                    "email_hash": email_hash,
                    "failure_count": fail_count,
                    "reason": body.get("msg", body.get("error_description", "unknown")),
                },
                ip=ip,
                user_agent=user_agent,
            )
            raise AuthenticationError("Invalid email or password.")

        # Success
        await reset_failed_login(self._redis, email_hash)

        user_id = body.get("user", {}).get("id")
        await self._audit(
            user_id=user_id,
            event_type="login_success",
            event_data={"email_hash": email_hash},
            ip=ip,
            user_agent=user_agent,
        )

        return self._build_auth_response(body)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    async def logout(self, access_token: str) -> None:
        """Sign out the user via Supabase."""
        headers = {**_SUPABASE_HEADERS, "Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{_AUTH_BASE}/logout", headers=headers)

        if resp.status_code >= 400:
            logger.warning("Supabase logout error", status=resp.status_code)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    async def refresh(self, refresh_token: str) -> dict:
        """Refresh session tokens via Supabase."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{_AUTH_BASE}/token?grant_type=refresh_token",
                headers=_SUPABASE_HEADERS,
                json={"refresh_token": refresh_token},
            )

        body = resp.json()

        if resp.status_code >= 400:
            raise AuthenticationError(
                body.get("msg", body.get("error_description", "Token refresh failed."))
            )

        return self._build_auth_response(body)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _audit(
        self,
        user_id: str | None,
        event_type: str,
        event_data: dict,
        ip: str,
        user_agent: str,
    ) -> None:
        """Insert an audit log row."""
        try:
            log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data,
                ip_address=ip,
                user_agent=user_agent,
            )
            self._db.add(log)
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            logger.warning("Failed to write audit log", event_type=event_type, exc_info=True)

    @staticmethod
    def _build_auth_response(body: dict) -> dict:
        """Normalise Supabase response into our AuthResponse shape."""
        user_data = body.get("user") or body
        user_meta = user_data.get("user_metadata", {})

        email_verified = False
        if user_data.get("email_confirmed_at"):
            email_verified = True

        return {
            "user": {
                "id": str(user_data.get("id", "")),
                "email": user_data.get("email", ""),
                "email_verified": email_verified,
                "role": user_meta.get("role", "user"),
                "subscription_tier": user_meta.get("subscription_tier", "free"),
            },
            "session": {
                "access_token": body.get("access_token", ""),
                "refresh_token": body.get("refresh_token", ""),
                "expires_in": body.get("expires_in", 0),
                "token_type": "bearer",
            },
        }
