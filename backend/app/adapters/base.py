"""Abstract base class for all broker adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

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


class BrokerAdapter(ABC):
    """Abstract broker adapter interface.

    All broker integrations (IBKR, Tradovate, Paper) must implement this interface.
    Methods are async to support WebSocket and REST-based brokers uniformly.
    """

    @abstractmethod
    async def connect(self) -> ConnectionStatus:
        """Establish connection to broker."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully close broker connection."""

    @abstractmethod
    async def place_order(self, order: OrderRequest) -> OrderResult:
        """Submit a single order to the broker."""

    @abstractmethod
    async def place_bracket_order(
        self,
        entry: OrderRequest,
        stop_loss: OrderRequest,
        take_profit: OrderRequest,
    ) -> BracketOrderResult:
        """Submit a bracket order (entry + SL + TP) as an atomic group."""

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> CancelResult:
        """Cancel a pending order."""

    @abstractmethod
    async def modify_order(
        self,
        broker_order_id: str,
        new_price: float | None = None,
        new_quantity: int | None = None,
    ) -> ModifyResult:
        """Modify a pending order's price or quantity."""

    @abstractmethod
    async def get_positions(self) -> list[PositionInfo]:
        """Get all open positions."""

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> OrderStatusInfo:
        """Get current status of a specific order."""

    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Get account balance and margin information."""

    @abstractmethod
    async def subscribe_order_updates(self) -> AsyncIterator[OrderResult]:
        """Stream real-time order fill updates."""

    @abstractmethod
    async def subscribe_position_updates(self) -> AsyncIterator[PositionInfo]:
        """Stream real-time position P&L updates."""
