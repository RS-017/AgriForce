"""routers/admin.py — Admin-only user management and reports."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.permissions import require_admin
from database import get_db
from models.users import User
from services.report_service import exportReport

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/users/{userId}")
async def viewUserProfile(
    userId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.farmer_profile),
            selectinload(User.worker_profile),
        )
        .where(User.id == userId)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "phone": user.phone,
        "email": user.email,
        "role": user.role.value,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "created_at": str(user.created_at),
        "farmer_profile": {
            "farm_size": user.farmer_profile.farm_size,
            "primary_crop": user.farmer_profile.primary_crop,
            "district": user.farmer_profile.district,
        } if user.farmer_profile else None,
        "worker_profile": {
            "experience_years": user.worker_profile.experience_years,
            "daily_wage": user.worker_profile.daily_wage,
        } if user.worker_profile else None,
    }


@router.patch("/users/{userId}/approve")
async def approveUser(
    userId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == userId))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    user.is_active = True
    await db.commit()
    return {"message": "User approved", "userId": str(userId)}


@router.patch("/users/{userId}/deactivate")
async def deactivateUser(
    userId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == userId))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.commit()
    return {"message": "User deactivated", "userId": str(userId)}


@router.get("/reports/export")
async def exportReport_route(
    report_type: str,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await exportReport(db, report_type, start_date, end_date)
