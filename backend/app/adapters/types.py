"""Data types for broker adapter responses."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ConnectionStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    ERROR = "ERROR"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class BracketRole(str, Enum):
    ENTRY = "ENTRY"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


@dataclass
class OrderRequest:
    """Order submission request to broker."""

    instrument_symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Decimal | None = None  # for LIMIT/STOP
    stop_price: Decimal | None = None  # for STOP_LIMIT
    time_in_force: str = "GTC"
    bracket_role: BracketRole = BracketRole.ENTRY
    bracket_group_id: str | None = None
    client_order_id: str | None = None


@dataclass
class OrderResult:
    """Result of an order submission."""

    broker_order_id: str
    status: str  # 'SUBMITTED', 'FILLED', 'REJECTED'
    fill_price: Decimal | None = None
    fill_quantity: int | None = None
    commission: Decimal | None = None
    message: str = ""
    timestamp: datetime | None = None


@dataclass
class BracketOrderResult:
    """Result of a bracket order submission (entry + SL + TP)."""

    entry: OrderResult
    stop_loss: OrderResult
    take_profit: OrderResult
    bracket_group_id: str = ""


@dataclass
class CancelResult:
    """Result of an order cancellation."""

    broker_order_id: str
    success: bool
    message: str = ""


@dataclass
class ModifyResult:
    """Result of an order modification."""

    broker_order_id: str
    success: bool
    new_price: Decimal | None = None
    message: str = ""


@dataclass
class AccountInfo:
    """Broker account information."""

    account_id: str
    balance: Decimal
    buying_power: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    margin_used: Decimal
    currency: str = "USD"


@dataclass
class PositionInfo:
    """Broker position information."""

    instrument_symbol: str
    quantity: int
    average_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    side: str  # "LONG" or "SHORT"


@dataclass
class OrderStatusInfo:
    """Current order status from broker."""

    broker_order_id: str
    status: str
    fill_price: Decimal | None = None
    filled_quantity: int | None = None
    remaining_quantity: int | None = None
    timestamp: datetime | None = None
