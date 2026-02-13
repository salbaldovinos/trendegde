"""Broker adapter registry — returns the correct adapter for a user's trading mode."""
from __future__ import annotations

import uuid

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BrokerAdapter
from app.adapters.exceptions import BrokerConnectionError
from app.adapters.ibkr import IBKRAdapter
from app.adapters.paper import PaperBrokerAdapter
from app.adapters.tradovate import TradovateAdapter
from app.core.logging import get_logger
from app.db.models.broker_connection import BrokerConnection

logger = get_logger("trendedge.adapters.registry")

_ADAPTER_MAP: dict[str, type[BrokerAdapter]] = {
    "ibkr": IBKRAdapter,
    "tradovate": TradovateAdapter,
}


async def get_adapter(
    user_id: uuid.UUID,
    db: AsyncSession,
    redis: Redis,
    is_paper: bool = True,
    slippage_ticks: int = 1,
) -> BrokerAdapter:
    """Return the appropriate broker adapter for the user.

    Paper mode (default) always returns PaperBrokerAdapter.
    Live mode looks up the user's active broker connection.
    """
    if is_paper:
        adapter = PaperBrokerAdapter(
            user_id=user_id,
            db=db,
            redis=redis,
            slippage_ticks=slippage_ticks,
        )
        await adapter.connect()
        return adapter

    # Live mode — find active broker connection
    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.user_id == user_id,
            BrokerConnection.status == "active",
            BrokerConnection.is_paper == False,  # noqa: E712
        ).limit(1)
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise BrokerConnectionError("live", "No active live broker connection found.")

    adapter_cls = _ADAPTER_MAP.get(connection.broker_type)
    if not adapter_cls:
        raise BrokerConnectionError(
            connection.broker_type,
            f"Unsupported broker type: {connection.broker_type}",
        )

    # For now, live adapters are stubs
    raise BrokerConnectionError(
        connection.broker_type, "Live trading not yet available. Use paper mode."
    )
