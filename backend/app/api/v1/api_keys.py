"""API key management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.requests.api_key import CreateApiKeyRequest
from app.schemas.responses.api_key import (
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
)
from app.services import api_key_service

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

_WEBHOOK_BASE_URL = "https://api.trendedge.io/v1/webhooks/tradingview"


@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyListResponse:
    """List all API keys for the authenticated user."""
    keys = await api_key_service.list_keys(user_id, db)
    return ApiKeyListResponse(keys=[ApiKeyResponse.model_validate(k) for k in keys])


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: CreateApiKeyRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedResponse:
    """Create a new API key. The full key is returned only once."""
    api_key, full_key = await api_key_service.create_key(
        user_id=user_id,
        name=body.name,
        permissions=body.permissions,
        expires_in_days=body.expires_in_days,
        db=db,
    )
    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        permissions=api_key.permissions,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        request_count=api_key.request_count,
        full_key=full_key,
        webhook_url=_WEBHOOK_BASE_URL,
    )


@router.patch("/{key_id}/revoke", response_model=ApiKeyResponse)
async def revoke_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    """Revoke an active API key."""
    api_key = await api_key_service.revoke_key(user_id, key_id, db)
    return ApiKeyResponse.model_validate(api_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Hard delete a revoked API key."""
    await api_key_service.delete_key(user_id, key_id, db)
