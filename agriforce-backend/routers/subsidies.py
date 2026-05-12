"""routers/subsidies.py — Subsidy schemes, alerts, and eligibility."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.permissions import require_farmer
from database import get_db
from models.subsidies import SubsidyScheme
from models.users import User
from schemas.subsidies import (
    EligibilityRequest, EligibilityResult, SubsidyAlertOut, SubsidySchemeOut
)
from services.subsidy_service import checkSubsidyEligibility as _check

router = APIRouter(prefix="/api/v1/subsidies", tags=["Subsidies"])


@router.get("/alerts", response_model=list[SubsidyAlertOut])
async def loadSubsidyAlerts(
    region: str = Query(""),
    crop: str = Query(""),          # used by app.js
    crop_type: str = Query(""),     # kept for Swagger compat
    db: AsyncSession = Depends(get_db),
):
    """Return schemes with deadline within the next 30 days."""
    deadline_threshold = date.today() + timedelta(days=30)
    query = select(SubsidyScheme).where(SubsidyScheme.deadline <= deadline_threshold)
    result = await db.execute(query)
    schemes = result.scalars().all()

    alerts = []
    for s in schemes:
        if s.deadline:
            days_left = (s.deadline - date.today()).days
            alerts.append(SubsidyAlertOut(id=s.id, schemeName=s.name, deadlineDays=days_left))
    return alerts


@router.get("/", response_model=list[SubsidySchemeOut])
async def fetchSubsidySchemes(
    region: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),       # used by app.js
    crop_type: Optional[str] = Query(None),  # kept for Swagger compat
    db: AsyncSession = Depends(get_db),
):
    query = select(SubsidyScheme).options(selectinload(SubsidyScheme.crops))
    if region:
        query = query.where(SubsidyScheme.eligible_regions.any(region))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/check-eligibility", response_model=EligibilityResult)
async def checkSubsidyEligibility(
    body: EligibilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    return await _check(db, body.farmerProfile, body.schemeId)
