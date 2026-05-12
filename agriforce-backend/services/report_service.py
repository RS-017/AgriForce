"""report_service.py — CSV export via pandas + StreamingResponse."""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.jobs import JobPost, Application
from models.users import User, FarmerProfile, WorkerProfile
from models.equipment import RentalBooking


async def exportReport(
    db: AsyncSession,
    report_type: str,
    start_date: date,
    end_date: date,
) -> StreamingResponse:
    """Query data, convert to CSV, return as StreamingResponse."""

    rows = []

    if report_type == "users":
        result = await db.execute(
            select(User).where(User.created_at.between(start_date, end_date))
        )
        users = result.scalars().all()
        rows = [
            {
                "id": str(u.id),
                "phone": u.phone,
                "email": u.email,
                "role": u.role.value,
                "is_verified": u.is_verified,
                "is_active": u.is_active,
                "created_at": str(u.created_at),
            }
            for u in users
        ]

    elif report_type == "jobs":
        result = await db.execute(
            select(JobPost).where(JobPost.created_at.between(start_date, end_date))
        )
        jobs = result.scalars().all()
        rows = [
            {
                "id": str(j.id),
                "district": j.district,
                "workers_required": j.workers_required,
                "start_date": str(j.start_date),
                "end_date": str(j.end_date),
                "daily_wage_offered": j.daily_wage_offered,
                "status": j.status.value,
                "created_at": str(j.created_at),
            }
            for j in jobs
        ]

    elif report_type == "hires":
        result = await db.execute(
            select(Application).where(Application.applied_at.between(start_date, end_date))
        )
        apps = result.scalars().all()
        rows = [
            {
                "id": str(a.id),
                "job_id": str(a.job_id),
                "worker_id": str(a.worker_id),
                "status": a.status.value,
                "applied_at": str(a.applied_at),
            }
            for a in apps
        ]

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={report_type}-report.csv"
        },
    )
