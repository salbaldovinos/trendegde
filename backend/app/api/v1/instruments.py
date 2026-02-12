"""Instrument route handlers."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
from app.db.models.instrument import Instrument
from app.db.session import get_db
from app.schemas.responses.trendline import InstrumentListResponse, InstrumentResponse

router = APIRouter(prefix="/instruments", tags=["instruments"])


# ------------------------------------------------------------------
# GET /instruments
# ------------------------------------------------------------------


@router.get("", response_model=InstrumentListResponse)
async def list_instruments(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstrumentListResponse:
    """List all available instruments."""
    result = await db.execute(
        select(Instrument).where(Instrument.is_active.is_(True)).order_by(Instrument.symbol)
    )
    instruments = result.scalars().all()
    return InstrumentListResponse(
        instruments=[
            InstrumentResponse(
                id=str(i.id),
                symbol=i.symbol,
                name=i.name,
                exchange=i.exchange,
                asset_class=i.asset_class,
                tick_size=float(i.tick_size),
                tick_value=float(i.tick_value),
                contract_months=i.contract_months,
                current_contract=i.current_contract,
                roll_date=str(i.roll_date) if i.roll_date else None,
                is_active=i.is_active,
            )
            for i in instruments
        ]
    )


# ------------------------------------------------------------------
# GET /instruments/{instrument_id}
# ------------------------------------------------------------------


@router.get("/{instrument_id}", response_model=InstrumentResponse)
async def get_instrument(
    instrument_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstrumentResponse:
    """Get a single instrument's details."""
    result = await db.execute(
        select(Instrument).where(
            Instrument.id == instrument_id,
            Instrument.is_active.is_(True),
        )
    )
    inst = result.scalar_one_or_none()
    if not inst:
        raise NotFoundError("Instrument", instrument_id)
    return InstrumentResponse(
        id=str(inst.id),
        symbol=inst.symbol,
        name=inst.name,
        exchange=inst.exchange,
        asset_class=inst.asset_class,
        tick_size=float(inst.tick_size),
        tick_value=float(inst.tick_value),
        contract_months=inst.contract_months,
        current_contract=inst.current_contract,
        roll_date=str(inst.roll_date) if inst.roll_date else None,
        is_active=inst.is_active,
    )
