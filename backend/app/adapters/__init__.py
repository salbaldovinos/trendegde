"""Broker adapter layer — abstract interface, implementations, and registry."""
from __future__ import annotations

from app.adapters.base import BrokerAdapter
from app.adapters.exceptions import (
    BrokerConnectionError,
    InsufficientMarginError,
    InvalidModificationError,
    InvalidSymbolError,
    OrderNotFoundError,
    OrderRejectedError,
)
from app.adapters.paper import PaperBrokerAdapter
from app.adapters.registry import get_adapter
from app.adapters.types import (
    AccountInfo,
    BracketOrderResult,
    BracketRole,
    CancelResult,
    ConnectionStatus,
    ModifyResult,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatusInfo,
    OrderType,
    PositionInfo,
)

__all__ = [
    "BrokerAdapter",
    "PaperBrokerAdapter",
    "get_adapter",
    "AccountInfo",
    "BracketOrderResult",
    "BracketRole",
    "CancelResult",
    "ConnectionStatus",
    "ModifyResult",
    "OrderRequest",
    "OrderResult",
    "OrderSide",
    "OrderStatusInfo",
    "OrderType",
    "PositionInfo",
    "BrokerConnectionError",
    "InsufficientMarginError",
    "InvalidModificationError",
    "InvalidSymbolError",
    "OrderNotFoundError",
    "OrderRejectedError",
]
