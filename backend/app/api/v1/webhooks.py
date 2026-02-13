"""Webhook route handlers — public endpoints authenticated by webhook_id."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.core.redis import get_redis
from app.db.models.webhook_url import WebhookUrl
from app.db.session import get_db
from app.schemas.requests.signal_request import WebhookSignalPayload
from app.schemas.responses.signal_response import SignalResponse
from app.services.signal_service import SignalService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _verify_webhook_signature(
    webhook_id: str,
    request: Request,
    db: AsyncSession,
) -> None:
    """Verify HMAC-SHA256 signature if the webhook has a secret configured."""
    stmt = select(WebhookUrl).where(WebhookUrl.webhook_id == webhook_id)
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()

    if webhook is None or not webhook.webhook_secret:
        return

    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        raise ForbiddenError("Missing X-Webhook-Signature header")

    body_bytes = await request.body()
    expected = hmac.new(
        webhook.webhook_secret.encode(), body_bytes, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise ForbiddenError("Invalid webhook signature")


@router.post("/tradingview/{webhook_id}", response_model=SignalResponse, status_code=201)
async def receive_tradingview_webhook(
    webhook_id: str,
    request: Request,
    body: WebhookSignalPayload,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SignalResponse:
    """Process an inbound TradingView webhook signal.

    This endpoint is PUBLIC — authenticated by webhook_id path param.
    No JWT required.
    """
    await _verify_webhook_signature(webhook_id, request, db)

    svc = SignalService(db, redis)
    signal = await svc.process_webhook_signal(webhook_id, body.model_dump())

    data = SignalService._signal_to_dict(signal)
    from datetime import datetime

    return SignalResponse(
        id=data["id"],
        source=data["source"],
        status=data["status"],
        instrument_symbol=data["instrument_symbol"],
        direction=data["direction"],
        entry_type=data["entry_type"],
        entry_price=data["entry_price"],
        stop_loss_price=data.get("stop_loss_price"),
        take_profit_price=data.get("take_profit_price"),
        quantity=data.get("quantity"),
        trendline_id=data.get("trendline_id"),
        trendline_grade=data.get("trendline_grade"),
        enrichment_data=data.get("enrichment_data"),
        rejection_reason=data.get("rejection_reason"),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )
