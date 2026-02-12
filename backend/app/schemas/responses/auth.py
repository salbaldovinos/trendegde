"""Pydantic response models for authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Public user representation."""

    id: str
    email: str
    email_verified: bool
    role: str
    subscription_tier: str


class SessionResponse(BaseModel):
    """Token session data."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Combined auth response with user and session."""

    user: UserResponse
    session: SessionResponse
    message: str | None = None


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
