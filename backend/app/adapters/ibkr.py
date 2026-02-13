"""Interactive Brokers adapter stub (Phase 2 implementation)."""
from __future__ import annotations

from collections.abc import AsyncIterator

from app.adapters.base import BrokerAdapter
from app.adapters.types import (
    AccountInfo,
    BracketOrderResult,
    CancelResult,
    ConnectionStatus,
    ModifyResult,
    OrderRequest,
    OrderResult,
    OrderStatusInfo,
    PositionInfo,
)


class IBKRAdapter(BrokerAdapter):
    """Interactive Brokers adapter using ib_async (TWS API).

    Stub implementation — all methods raise NotImplementedError.
    Full implementation planned for Phase 2.
    """

    async def connect(self) -> ConnectionStatus:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def disconnect(self) -> None:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def place_order(self, order: OrderRequest) -> OrderResult:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def place_bracket_order(
        self,
        entry: OrderRequest,
        stop_loss: OrderRequest,
        take_profit: OrderRequest,
    ) -> BracketOrderResult:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def cancel_order(self, broker_order_id: str) -> CancelResult:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def modify_order(
        self,
        broker_order_id: str,
        new_price: float | None = None,
        new_quantity: int | None = None,
    ) -> ModifyResult:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def get_positions(self) -> list[PositionInfo]:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def get_order_status(self, broker_order_id: str) -> OrderStatusInfo:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def get_account_info(self) -> AccountInfo:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def subscribe_order_updates(self) -> AsyncIterator[OrderResult]:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")

    async def subscribe_position_updates(self) -> AsyncIterator[PositionInfo]:
        raise NotImplementedError("IBKR adapter: Phase 2 implementation")
