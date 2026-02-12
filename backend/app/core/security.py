"""JWT validation and authentication dependencies for Supabase tokens."""

from __future__ import annotations

from fastapi import Request
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger("trendedge.security")

_JWT_ALGORITHM = "HS256"
_JWT_AUDIENCE = "authenticated"


async def validate_jwt(token: str) -> dict:
    """Validate a Supabase JWT and return decoded claims.

    Checks signature (HS256), expiration, and audience.
    Returns the full decoded claims dict on success.
    """
    try:
        claims = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[_JWT_ALGORITHM],
            audience=_JWT_AUDIENCE,
        )
    except ExpiredSignatureError:
        raise AuthenticationError("Token has expired. Please refresh.")
    except JWTError:
        raise AuthenticationError("Invalid authentication token.")

    if "sub" not in claims:
        raise AuthenticationError("Invalid authentication token.")

    return claims


async def get_current_user(request: Request) -> str:
    """FastAPI dependency that extracts and validates JWT from Authorization header.

    Sets request.state.user_id on success. Returns the user_id string (UUID).
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError("Authentication required.")

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer" or not parts[1].strip():
        raise AuthenticationError("Invalid authentication token.")

    token = parts[1].strip()
    claims = await validate_jwt(token)
    user_id: str = claims["sub"]

    request.state.user_id = user_id
    return user_id
