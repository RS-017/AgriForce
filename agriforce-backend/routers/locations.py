"""routers/locations.py — State/District/Taluk data."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.locations import District, State, Taluk
from schemas.locations import DistrictOut, TalukOut

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])


@router.get("/")
async def fetchLocationData(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return districts for a state, or taluks for a district."""
    if district:
        # Return taluks for the district
        dist_result = await db.execute(
            select(District).where(District.name.ilike(f"%{district}%"))
        )
        dist = dist_result.scalar_one_or_none()
        if not dist:
            return []
        taluk_result = await db.execute(
            select(Taluk).where(Taluk.district_id == dist.id)
        )
        taluks = taluk_result.scalars().all()
        return [TalukOut.model_validate(t) for t in taluks]

    elif state:
        # Return districts for the state
        state_result = await db.execute(
            select(State).where(State.name.ilike(f"%{state}%"))
        )
        st = state_result.scalar_one_or_none()
        if not st:
            return []
        dist_result = await db.execute(
            select(District).where(District.state_id == st.id)
        )
        districts = dist_result.scalars().all()
        return [DistrictOut.model_validate(d) for d in districts]

    return []
