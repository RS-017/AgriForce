"""routers/applications.py — Job application endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.permissions import require_worker
from database import get_db
from models.jobs import Application
from models.users import User, WorkerProfile
from schemas.applications import ApplicationCreate, ApplicationOut
from services import job_service

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


@router.post("/apply", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def applyForJob(
    body: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_worker),
):
    try:
        application = await job_service.applyForJob(db, body.jobId, body.workerId)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return application


@router.get("/worker/{workerId}", response_model=list[ApplicationOut])
async def loadMyApplications(
    workerId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_worker),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.worker_id == workerId)
        .order_by(Application.applied_at.desc())
    )
    apps = result.scalars().all()

    out = []
    for app in apps:
        out.append(
            ApplicationOut(
                id=app.id,
                job_id=app.job_id,
                worker_id=app.worker_id,
                status=app.status.value,
                applied_at=app.applied_at,
                jobTitle=f"{app.job.district} Harvest" if app.job else "—",
                appliedDate=app.applied_at.strftime("%d %b %Y") if app.applied_at else "—",
            )
        )
    return out
