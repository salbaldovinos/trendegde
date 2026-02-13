"""Broker adapter exceptions."""
from __future__ import annotations

from app.core.exceptions import BrokerError


class BrokerConnectionError(BrokerError):
    """Failed to connect to broker."""

    def __init__(self, broker_type: str, message: str = ""):
        msg = f"Failed to connect to {broker_type} broker."
        if message:
            msg = f"{msg} {message}"
        super().__init__(message=msg)


class OrderRejectedError(BrokerError):
    """Broker rejected the order."""

    def __init__(self, reason: str = "Order rejected by broker."):
        super().__init__(message=reason)


class InsufficientMarginError(BrokerError):
    """Insufficient margin for order."""

    def __init__(self, required: str = "", available: str = ""):
        msg = "Insufficient margin for order."
        if required and available:
            msg = f"Insufficient margin. Required: {required}, Available: {available}"
        super().__init__(message=msg)


class InvalidSymbolError(BrokerError):
    """Invalid or unsupported instrument symbol."""

    def __init__(self, symbol: str = ""):
        msg = f"Invalid instrument symbol: {symbol}" if symbol else "Invalid instrument symbol."
        super().__init__(message=msg)


class OrderNotFoundError(BrokerError):
    """Order not found in broker system."""

    def __init__(self, order_id: str = ""):
        msg = f"Order not found: {order_id}" if order_id else "Order not found."
        super().__init__(message=msg)


class InvalidModificationError(BrokerError):
    """Invalid order modification request."""

    def __init__(self, reason: str = ""):
        msg = f"Invalid order modification: {reason}" if reason else "Invalid order modification."
        super().__init__(message=msg)
