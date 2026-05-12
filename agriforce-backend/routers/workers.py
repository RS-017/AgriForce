"""routers/workers.py — Worker profile and recommendation endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth import get_current_user
from core.permissions import require_worker, require_farmer
from database import get_db
from models.jobs import Application, ApplicationStatus, JobPost
from models.users import User
from schemas.workers import EarningsOut, ProfileCompletionOut, RecommendedWorkerOut
from services import worker_service

router = APIRouter(prefix="/api/v1/workers", tags=["Workers"])


@router.get("/recommended/{farmerId}", response_model=list[RecommendedWorkerOut])
async def loadRecommendedWorkers(
    farmerId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    return await worker_service.loadRecommendedWorkers(db, farmerId)


@router.get("/{workerId}/profile-completion", response_model=ProfileCompletionOut)
async def calculateProfileCompletion(
    workerId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_worker),
):
    return await worker_service.calculateProfileCompletion(db, workerId)


@router.get("/{workerId}/earnings", response_model=EarningsOut)
async def renderEarningsChart(
    workerId: UUID,
    period: str = Query("3m", pattern="^(3m|6m|1y)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_worker),
):
    """Aggregate accepted applications × wage × days, grouped by month."""
    period_months = {"3m": 3, "6m": 6, "1y": 12}.get(period, 3)

    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(
            Application.worker_id == workerId,
            Application.status == ApplicationStatus.ACCEPTED,
        )
    )
    applications = result.scalars().all()

    # Group by month
    monthly: dict[str, float] = {}
    for app in applications:
        if app.job:
            days = (app.job.end_date - app.job.start_date).days or 1
            amount = days * app.job.daily_wage_offered
            month_key = app.job.start_date.strftime("%b %Y")
            monthly[month_key] = monthly.get(month_key, 0) + amount

    labels = list(monthly.keys())[-period_months:]
    earnings = [monthly[l] for l in labels]

    return EarningsOut(labels=labels, earnings=earnings)
