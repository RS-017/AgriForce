"""routers/crops.py — Crop peak-season data."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.crops import Crop

router = APIRouter(prefix="/api/v1/crops", tags=["Crops"])


@router.get("/peak-season/{cropType}")
async def autofillPeakSeason(cropType: str, db: AsyncSession = Depends(get_db)):
    """Return peak harvest start/end dates for a crop."""
    result = await db.execute(select(Crop).where(Crop.name.ilike(cropType)))
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop '{cropType}' not found")
    return {
        "cropType": crop.name,
        "startDate": str(crop.peak_harvest_start) if crop.peak_harvest_start else None,
        "endDate": str(crop.peak_harvest_end) if crop.peak_harvest_end else None,
        "season": crop.season.value if crop.season else None,
    }
