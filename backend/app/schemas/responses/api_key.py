"""Response schemas for API key management."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ApiKeyResponse(BaseModel):
    """Public API key info (never includes the full key)."""

    id: uuid.UUID
    name: str
    key_prefix: str
    permissions: list[str]
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    request_count: int

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned once on creation -- includes the full plaintext key."""

    full_key: str
    webhook_url: str
    message: str = "Your API key has been created. Copy it now -- you won't be able to see it again."


class ApiKeyListResponse(BaseModel):
    """Paginated list of API keys."""

    keys: list[ApiKeyResponse]
