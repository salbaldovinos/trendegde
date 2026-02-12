"""ORM model registry — import all models so Alembic can discover them."""

from __future__ import annotations

from app.db.models.alert import Alert
from app.db.models.api_key import ApiKey
from app.db.models.audit_log import AuditLog
from app.db.models.broker_connection import BrokerConnection
from app.db.models.candle import Candle
from app.db.models.instrument import Instrument
from app.db.models.pivot import Pivot
from app.db.models.trendline import Trendline
from app.db.models.trendline_event import TrendlineEvent
from app.db.models.user import User
from app.db.models.user_detection_config import UserDetectionConfig
from app.db.models.user_watchlist import UserWatchlist

__all__ = [
    "Alert",
    "ApiKey",
    "AuditLog",
    "BrokerConnection",
    "Candle",
    "Instrument",
    "Pivot",
    "Trendline",
    "TrendlineEvent",
    "User",
    "UserDetectionConfig",
    "UserWatchlist",
]
