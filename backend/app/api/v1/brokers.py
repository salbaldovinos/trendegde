"""Broker connection route handlers."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.requests.broker import (
    CreateBrokerConnectionRequest,
    TestBrokerConnectionRequest,
    UpdateBrokerConnectionRequest,
)
from app.schemas.responses.broker import (
    BrokerConnectionListResponse,
    BrokerConnectionResponse,
    TestConnectionResponse,
)
from app.services.broker_service import BrokerService

router = APIRouter(prefix="/broker-connections", tags=["brokers"])


def _to_response(conn) -> BrokerConnectionResponse:
    """Map a BrokerConnection ORM instance to the response model."""
    return BrokerConnectionResponse(
        id=str(conn.id),
        broker_type=conn.broker_type,
        display_name=conn.display_name,
        status=conn.status,
        last_connected_at=conn.last_connected_at,
        last_error=conn.last_error,
        account_id=conn.account_id,
        is_paper=conn.is_paper,
        created_at=conn.created_at,
    )


# ------------------------------------------------------------------
# GET /broker-connections
# ------------------------------------------------------------------

@router.get("", response_model=BrokerConnectionListResponse)
async def list_broker_connections(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrokerConnectionListResponse:
    """List all broker connections for the authenticated user."""
    svc = BrokerService(db)
    connections = await svc.list_connections(user_id)
    return BrokerConnectionListResponse(
        connections=[_to_response(c) for c in connections]
    )


# ------------------------------------------------------------------
# POST /broker-connections
# ------------------------------------------------------------------

@router.post("", response_model=BrokerConnectionResponse, status_code=201)
async def create_broker_connection(
    body: CreateBrokerConnectionRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrokerConnectionResponse:
    """Create a new broker connection with tier enforcement."""
    svc = BrokerService(db)
    connection = await svc.create_connection(user_id, body)
    return _to_response(connection)


# ------------------------------------------------------------------
# POST /broker-connections/test
# ------------------------------------------------------------------

@router.post("/test", response_model=TestConnectionResponse)
async def test_broker_connection(
    body: TestBrokerConnectionRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestConnectionResponse:
    """Test broker credentials before saving."""
    svc = BrokerService(db)
    result = await svc.test_connection(body.broker_type.value, body.credentials)
    return TestConnectionResponse(**result)


# ------------------------------------------------------------------
# POST /broker-connections/{connection_id}/test
# ------------------------------------------------------------------

@router.post("/{connection_id}/test", response_model=TestConnectionResponse)
async def test_existing_broker_connection(
    connection_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestConnectionResponse:
    """Test an existing broker connection by decrypting stored credentials."""
    svc = BrokerService(db)
    result = await svc.test_existing_connection(user_id, connection_id)
    return TestConnectionResponse(**result)


# ------------------------------------------------------------------
# PATCH /broker-connections/{connection_id}
# ------------------------------------------------------------------

@router.patch("/{connection_id}", response_model=BrokerConnectionResponse)
async def update_broker_connection(
    connection_id: str,
    body: UpdateBrokerConnectionRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrokerConnectionResponse:
    """Update display name, credentials, or status of a broker connection."""
    svc = BrokerService(db)
    connection = await svc.update_connection(user_id, connection_id, body)
    return _to_response(connection)


# ------------------------------------------------------------------
# DELETE /broker-connections/{connection_id}
# ------------------------------------------------------------------

@router.delete("/{connection_id}", status_code=200)
async def delete_broker_connection(
    connection_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a broker connection (hard delete)."""
    svc = BrokerService(db)
    await svc.delete_connection(user_id, connection_id)
    return {"message": "Broker connection removed."}
