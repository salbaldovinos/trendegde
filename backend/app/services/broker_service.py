"""Business logic for broker connection management."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.db.models.broker_connection import BrokerConnection
from app.db.models.user import User
from app.schemas.requests.broker import (
    CreateBrokerConnectionRequest,
    UpdateBrokerConnectionRequest,
)
from app.services.encryption_service import decrypt_credentials, encrypt_credentials

logger = get_logger("trendedge.broker_service")

# Tier limits: max broker connections per subscription tier
_TIER_LIMITS: dict[str, int | None] = {
    "free": 0,
    "trader": 1,
    "pro": 3,
    "team": None,  # unlimited
}

_TIER_MESSAGES: dict[str, str] = {
    "free": (
        "Your Free plan does not include broker connections. "
        "Upgrade to Trader ($49/mo) to connect a broker."
    ),
    "trader": (
        "Your Trader plan supports up to 1 broker connection. "
        "Upgrade to Pro ($99/mo) for up to 3 connections."
    ),
    "pro": (
        "Your Pro plan supports up to 3 broker connections. "
        "Upgrade to Team ($199/mo) for unlimited connections."
    ),
}

# 30-second timeout for test connections
_TEST_TIMEOUT_SECONDS = 30


class BrokerService:
    """Handles broker connection CRUD, tier enforcement, and credential encryption."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    async def list_connections(self, user_id: str) -> list[BrokerConnection]:
        """Return all broker connections for a user (no credential fields)."""
        result = await self._db.execute(
            select(BrokerConnection)
            .where(BrokerConnection.user_id == uuid.UUID(user_id))
            .order_by(BrokerConnection.created_at.desc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_connection(
        self, user_id: str, data: CreateBrokerConnectionRequest
    ) -> BrokerConnection:
        """Create a broker connection after tier check and encryption."""
        uid = uuid.UUID(user_id)

        # Fetch user tier
        tier = await self._get_user_tier(uid)
        await self._enforce_tier_limit(uid, tier)

        # Check duplicate display name (case-insensitive)
        await self._check_duplicate_name(uid, data.display_name)

        # Generate ID for key derivation, then encrypt
        connection_id = uuid.uuid4()
        ciphertext, iv, key_id = encrypt_credentials(connection_id, data.credentials)

        connection = BrokerConnection(
            id=connection_id,
            user_id=uid,
            broker_type=data.broker_type.value,
            display_name=data.display_name,
            credentials_encrypted=ciphertext,
            credentials_iv=iv,
            credentials_key_id=key_id,
            status="active",
            is_paper=data.is_paper,
            last_connected_at=datetime.now(UTC),
        )

        self._db.add(connection)
        await self._db.commit()
        await self._db.refresh(connection)

        logger.info(
            "Broker connection created",
            user_id=user_id,
            broker_type=data.broker_type.value,
            connection_id=str(connection_id),
        )
        return connection

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_connection(
        self,
        user_id: str,
        connection_id: str,
        data: UpdateBrokerConnectionRequest,
    ) -> BrokerConnection:
        """Update a broker connection. Re-encrypts if credentials are changed."""
        connection = await self._get_owned_connection(user_id, connection_id)

        if data.display_name is not None and data.display_name != connection.display_name:
            await self._check_duplicate_name(
                uuid.UUID(user_id), data.display_name, exclude_id=connection.id
            )
            connection.display_name = data.display_name

        if data.credentials is not None:
            ciphertext, iv, key_id = encrypt_credentials(connection.id, data.credentials)
            connection.credentials_encrypted = ciphertext
            connection.credentials_iv = iv
            connection.credentials_key_id = key_id

        if data.status is not None:
            connection.status = data.status.value

        await self._db.commit()
        await self._db.refresh(connection)

        logger.info(
            "Broker connection updated",
            user_id=user_id,
            connection_id=connection_id,
        )
        return connection

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_connection(self, user_id: str, connection_id: str) -> None:
        """Hard-delete a broker connection."""
        connection = await self._get_owned_connection(user_id, connection_id)
        await self._db.delete(connection)
        await self._db.commit()

        logger.info(
            "Broker connection deleted",
            user_id=user_id,
            connection_id=connection_id,
        )

    # ------------------------------------------------------------------
    # Test (unsaved credentials)
    # ------------------------------------------------------------------

    async def test_connection(
        self, broker_type: str, credentials: dict
    ) -> dict:
        """Test broker connectivity with a 30-second timeout.

        Returns a dict with success, account_id, balance, currency, or error.
        In Phase 1, this is a stub that validates credential shape.
        Actual broker adapters are implemented in FSD-003c.
        """
        try:
            result = await asyncio.wait_for(
                self._do_test_connection(broker_type, credentials),
                timeout=_TEST_TIMEOUT_SECONDS,
            )
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Connection test timed out. Please check your broker is running and try again.",
            }
        except Exception as exc:
            logger.warning(
                "Broker test connection failed",
                broker_type=broker_type,
                error=str(exc),
            )
            return {
                "success": False,
                "error": f"Unable to connect to {broker_type}. Please check your network and try again.",
            }

    # ------------------------------------------------------------------
    # Test (existing connection)
    # ------------------------------------------------------------------

    async def test_existing_connection(
        self, user_id: str, connection_id: str
    ) -> dict:
        """Test an already-saved broker connection by decrypting its credentials."""
        connection = await self._get_owned_connection(user_id, connection_id)

        credentials = decrypt_credentials(
            connection.id,
            connection.credentials_encrypted,
            connection.credentials_iv,
            connection.credentials_key_id,
        )

        return await self.test_connection(connection.broker_type, credentials)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _do_test_connection(self, broker_type: str, credentials: dict) -> dict:
        """Stub broker test — validates credential shape.

        Real broker adapter calls (IBKR, Tradovate, Webull) will replace this
        when FSD-003c broker adapters are implemented.
        """
        if broker_type == "ibkr":
            required = {"host", "port", "client_id", "account"}
            missing = required - set(credentials.keys())
            if missing:
                return {"success": False, "error": f"Missing IBKR fields: {', '.join(sorted(missing))}"}
            return {
                "success": True,
                "account_id": credentials.get("account"),
                "balance": None,
                "currency": "USD",
            }

        if broker_type == "tradovate":
            required = {"username", "password", "app_id", "app_version", "cid", "sec"}
            missing = required - set(credentials.keys())
            if missing:
                return {"success": False, "error": f"Missing Tradovate fields: {', '.join(sorted(missing))}"}
            return {
                "success": True,
                "account_id": credentials.get("username"),
                "balance": None,
                "currency": "USD",
            }

        if broker_type == "webull":
            required = {"app_key", "app_secret"}
            missing = required - set(credentials.keys())
            if missing:
                return {"success": False, "error": f"Missing Webull fields: {', '.join(sorted(missing))}"}
            return {
                "success": True,
                "account_id": credentials.get("account_id"),
                "balance": None,
                "currency": "USD",
            }

        return {"success": False, "error": f"Unsupported broker type: {broker_type}"}

    async def _get_user_tier(self, user_id: uuid.UUID) -> str:
        """Fetch the user's subscription tier."""
        result = await self._db.execute(
            select(User.subscription_tier).where(User.id == user_id)
        )
        tier = result.scalar_one_or_none()
        if tier is None:
            raise NotFoundError("User", str(user_id))
        return tier

    async def _enforce_tier_limit(self, user_id: uuid.UUID, tier: str) -> None:
        """Raise ForbiddenError if user is at their tier's connection limit."""
        limit = _TIER_LIMITS.get(tier)
        if limit == 0:
            raise ForbiddenError(_TIER_MESSAGES["free"])
        if limit is None:
            return  # unlimited

        # Count non-disconnected connections
        result = await self._db.execute(
            select(func.count())
            .select_from(BrokerConnection)
            .where(
                BrokerConnection.user_id == user_id,
                BrokerConnection.status != "disconnected",
            )
        )
        count = result.scalar_one()

        if count >= limit:
            message = _TIER_MESSAGES.get(tier, f"You have reached the maximum of {limit} broker connections for your plan.")
            raise ForbiddenError(message)

    async def _check_duplicate_name(
        self,
        user_id: uuid.UUID,
        display_name: str,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        """Raise ConflictError if display_name already exists for this user (case-insensitive)."""
        query = (
            select(func.count())
            .select_from(BrokerConnection)
            .where(
                BrokerConnection.user_id == user_id,
                func.lower(BrokerConnection.display_name) == display_name.lower(),
            )
        )
        if exclude_id is not None:
            query = query.where(BrokerConnection.id != exclude_id)

        result = await self._db.execute(query)
        if result.scalar_one() > 0:
            raise ConflictError(
                f"You already have a connection named '{display_name}'. Please choose a different name."
            )

    async def _get_owned_connection(
        self, user_id: str, connection_id: str
    ) -> BrokerConnection:
        """Fetch a broker connection owned by the user, or raise NotFoundError."""
        result = await self._db.execute(
            select(BrokerConnection).where(
                BrokerConnection.id == uuid.UUID(connection_id),
                BrokerConnection.user_id == uuid.UUID(user_id),
            )
        )
        connection = result.scalar_one_or_none()
        if connection is None:
            raise NotFoundError("Broker connection", connection_id)
        return connection
