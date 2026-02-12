"""ORM model registry — import all models so Alembic can discover them."""

from __future__ import annotations

from app.db.models.audit_log import AuditLog
from app.db.models.user import User

__all__ = ["AuditLog", "User"]
