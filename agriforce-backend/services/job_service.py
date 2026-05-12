"""job_service.py — Job application and rental booking logic."""
from __future__ import annotations

import uuid
from datetime import date
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.jobs import Application, ApplicationStatus, JobPost
from models.equipment import Equipment, RentalBooking
from models.notifications import NotificationType
from models.users import FarmerProfile


async def applyForJob(db: AsyncSession, job_id: UUID, worker_id: UUID) -> Application:
    """
    Insert an application preventing duplicates via UNIQUE constraint.
    On success, notify the farmer.
    """
    application = Application(
        id=uuid.uuid4(),
        job_id=job_id,
        worker_id=worker_id,
        status=ApplicationStatus.PENDING,
    )
    db.add(application)
    try:
        await db.commit()
        await db.refresh(application)
    except IntegrityError:
        await db.rollback()
        raise ValueError("You have already applied for this job.")

    # Notify the farmer
    job_result = await db.execute(
        select(JobPost).options(selectinload(JobPost.farmer)).where(JobPost.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if job and job.farmer:
        from services.notification_service import createNotification
        farmer_user_id = str(job.farmer.user_id)
        await createNotification(
            db,
            farmer_user_id,
            f"New application received for your {job.district} job post.",
            NotificationType.APPLICATION_UPDATE,
        )

    return application


async def submitRentalBooking(db: AsyncSession, equipment_id: UUID, farmer_id: UUID,
                              start_date: date, end_date: date) -> RentalBooking:
    """Check for booking conflicts then insert."""
    # Overlap check: NOT (existing.end_date <= new.start OR existing.start_date >= new.end)
    overlap_result = await db.execute(
        select(RentalBooking).where(
            and_(
                RentalBooking.equipment_id == equipment_id,
                ~or_(
                    RentalBooking.end_date <= start_date,
                    RentalBooking.start_date >= end_date,
                ),
            )
        )
    )
    if overlap_result.scalar_one_or_none():
        raise ValueError("Equipment is already booked for the selected dates.")

    eq_result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = eq_result.scalar_one_or_none()
    if not equipment:
        raise ValueError("Equipment not found.")

    days = (end_date - start_date).days or 1
    total_cost = equipment.daily_rate * days

    booking = RentalBooking(
        id=uuid.uuid4(),
        equipment_id=equipment_id,
        farmer_id=farmer_id,
        start_date=start_date,
        end_date=end_date,
        total_cost=total_cost,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
