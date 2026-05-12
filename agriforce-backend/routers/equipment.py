"""routers/equipment.py — Equipment listing, detail, booking, provider contact."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.permissions import require_farmer
from database import get_db
from models.equipment import Equipment, RentalBooking
from models.users import User
from schemas.equipment import EquipmentOut, RentalBookingCreate, RentalBookingOut
from services import job_service

router = APIRouter(prefix="/api/v1/equipment", tags=["Equipment"])


@router.get("/", response_model=list[EquipmentOut])
async def applyEquipmentFilters(
    type: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    min_rate: Optional[float] = Query(None),
    max_rate: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Equipment)
    if type:
        query = query.where(Equipment.type.ilike(f"%{type}%"))
    if district:
        query = query.where(Equipment.district.ilike(f"%{district}%"))
    if min_rate is not None:
        query = query.where(Equipment.daily_rate >= min_rate)
    if max_rate is not None:
        query = query.where(Equipment.daily_rate <= max_rate)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/provider/{providerId}")
async def contactEquipmentProvider(
    providerId: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Equipment).where(Equipment.provider_id == providerId).limit(1)
    )
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(status_code=404, detail="Provider not found")

    from models.users import User
    user_result = await db.execute(select(User).where(User.id == providerId))
    user = user_result.scalar_one_or_none()
    return {
        "phone": user.phone if user else None,
        "email": user.email if user else None,
    }


@router.get("/{equipmentId}", response_model=EquipmentOut)
async def openEquipmentModal(
    equipmentId: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Equipment)
        .options(selectinload(Equipment.bookings))
        .where(Equipment.id == equipmentId)
    )
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@router.post("/book", response_model=RentalBookingOut, status_code=status.HTTP_201_CREATED)
async def submitRentalBooking(
    body: RentalBookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    from models.users import FarmerProfile
    fp_result = await db.execute(
        select(FarmerProfile).where(FarmerProfile.user_id == current_user.id)
    )
    farmer = fp_result.scalar_one_or_none()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    try:
        booking = await job_service.submitRentalBooking(
            db, body.equipmentId, farmer.id, body.startDate, body.endDate
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return booking
