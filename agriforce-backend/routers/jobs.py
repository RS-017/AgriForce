"""routers/jobs.py — Job post CRUD + worker broadcast."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.permissions import require_farmer
from database import get_db
from models.jobs import Application, JobPost, JobStatus
from models.users import FarmerProfile, User
from schemas.jobs import JobPostCreate, JobPostOut
from services.notification_service import manager

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("/create", response_model=JobPostOut, status_code=status.HTTP_201_CREATED)
async def submitJobPost(
    body: JobPostCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    # Get the farmer profile
    fp_result = await db.execute(
        select(FarmerProfile).where(FarmerProfile.user_id == current_user.id)
    )
    farmer = fp_result.scalar_one_or_none()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    job = JobPost(
        id=uuid.uuid4(),
        farmer_id=farmer.id,
        crop_type_id=body.crop_type_id,
        district=body.district,
        taluk=body.taluk,
        workers_required=body.workers_required,
        start_date=body.start_date,
        end_date=body.end_date,
        daily_wage_offered=body.daily_wage_offered,
        status=JobStatus.OPEN,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Broadcast to workers in same district via WebSocket (background)
    background_tasks.add_task(
        manager.broadcast,
        {
            "id": str(job.id),
            "cropType": str(body.crop_type_id),
            "district": job.district,
            "startDate": str(job.start_date),
            "workersNeeded": job.workers_required,
            "dailyWage": job.daily_wage_offered,
        },
    )
    return job


@router.get("/available", response_model=list[JobPostOut])
async def fetchAvailableJobs(
    crop_type: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    min_wage: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(JobPost).where(JobPost.status == JobStatus.OPEN)
    if district:
        query = query.where(JobPost.district.ilike(f"%{district}%"))
    if start_date:
        query = query.where(JobPost.start_date >= start_date)
    if min_wage:
        query = query.where(JobPost.daily_wage_offered >= min_wage)
    result = await db.execute(query.order_by(JobPost.created_at.desc()))
    return result.scalars().all()


@router.get("/{jobId}", response_model=JobPostOut)
async def editJobPost(
    jobId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    result = await db.execute(select(JobPost).where(JobPost.id == jobId))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{jobId}", status_code=status.HTTP_204_NO_CONTENT)
async def deleteJobPost(
    jobId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    fp_result = await db.execute(
        select(FarmerProfile).where(FarmerProfile.user_id == current_user.id)
    )
    farmer = fp_result.scalar_one_or_none()

    result = await db.execute(select(JobPost).where(JobPost.id == jobId))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if farmer and job.farmer_id != farmer.id:
        raise HTTPException(status_code=403, detail="Not your job post")

    await db.delete(job)
    await db.commit()


@router.patch("/{jobId}/close", response_model=JobPostOut)
async def closeJobPost(
    jobId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_farmer),
):
    result = await db.execute(select(JobPost).where(JobPost.id == jobId))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.CLOSED
    await db.commit()
    await db.refresh(job)
    return job
