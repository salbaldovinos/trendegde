"""ORM model registry — import all models so Alembic can discover them."""

from __future__ import annotations

from app.db.models.alert import Alert
from app.db.models.api_key import ApiKey
from app.db.models.audit_log import AuditLog
from app.db.models.broker_connection import BrokerConnection
from app.db.models.candle import Candle
from app.db.models.contract_calendar import ContractCalendar
from app.db.models.contract_specification import ContractSpecification
from app.db.models.instrument import Instrument
from app.db.models.instrument_correlation import InstrumentCorrelation
from app.db.models.order import Order
from app.db.models.order_event import OrderEvent
from app.db.models.pivot import Pivot
from app.db.models.position import Position
from app.db.models.risk_check_audit import RiskCheckAudit
from app.db.models.risk_settings_changelog import RiskSettingsChangelog
from app.db.models.signal import Signal
from app.db.models.trendline import Trendline
from app.db.models.trendline_event import TrendlineEvent
from app.db.models.user import User
from app.db.models.user_detection_config import UserDetectionConfig
from app.db.models.user_risk_settings import UserRiskSettings
from app.db.models.user_watchlist import UserWatchlist
from app.db.models.webhook_url import WebhookUrl

__all__ = [
    "Alert",
    "ApiKey",
    "AuditLog",
    "BrokerConnection",
    "Candle",
    "ContractCalendar",
    "ContractSpecification",
    "Instrument",
    "InstrumentCorrelation",
    "Order",
    "OrderEvent",
    "Pivot",
    "Position",
    "RiskCheckAudit",
    "RiskSettingsChangelog",
    "Signal",
    "Trendline",
    "TrendlineEvent",
    "User",
    "UserDetectionConfig",
    "UserRiskSettings",
    "UserWatchlist",
    "WebhookUrl",
]
