"""worker_service.py — Farmer-side worker recommendation with scoring."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.users import FarmerProfile, WorkerProfile, WorkerSkill, Skill, AvailabilityStatus


async def loadRecommendedWorkers(db: AsyncSession, farmer_id: UUID) -> list[dict]:
    """
    Recommend workers for a farmer.
    Scoring: skill_overlap×0.4 + geo_proximity×0.3 + availability×0.2 + experience×0.1
    """
    # 1. Load farmer profile
    farmer_result = await db.execute(
        select(FarmerProfile).where(FarmerProfile.id == farmer_id)
    )
    farmer = farmer_result.scalar_one_or_none()
    if not farmer:
        return []

    # 2. Load all available workers with skills
    workers_result = await db.execute(
        select(WorkerProfile)
        .options(selectinload(WorkerProfile.skills), selectinload(WorkerProfile.user))
        .where(WorkerProfile.availability_status == AvailabilityStatus.AVAILABLE)
    )
    workers = workers_result.scalars().all()

    # 3. Score each worker
    scored = []
    for w in workers:
        skill_names = [s.name.lower() for s in w.skills]
        primary_crop_lower = (farmer.primary_crop or "").lower()

        # Skill overlap — crude check if any skill mentions the crop
        skill_overlap = 1.0 if any(primary_crop_lower in s for s in skill_names) else 0.3

        # Geo proximity — same district scores highest; simplified
        same_district = (farmer.district or "").lower() == (
            getattr(w.user, "district", "") or ""
        ).lower()
        geo_score = 1.0 if same_district else 0.4

        # Availability
        avail_score = 1.0 if w.availability_status == AvailabilityStatus.AVAILABLE else 0.0

        # Experience (normalised to max 10 yrs)
        exp_score = min((w.experience_years or 0) / 10.0, 1.0)

        total_score = (
            skill_overlap * 0.4
            + geo_score * 0.3
            + avail_score * 0.2
            + exp_score * 0.1
        )

        scored.append({
            "worker": w,
            "score": total_score,
        })

    # 4. Sort and return top 10
    scored.sort(key=lambda x: x["score"], reverse=True)
    result = []
    for entry in scored[:10]:
        w = entry["worker"]
        result.append({
            "id": str(w.id),
            "name": getattr(w.user, "phone", "Unknown"),
            "skills": [s.name for s in w.skills],
            "distance": None,  # Would need geo coords in production
            "dailyWage": w.daily_wage,
            "experience_years": w.experience_years,
            "availability_status": w.availability_status.value,
        })
    return result


async def calculateProfileCompletion(db: AsyncSession, worker_id: UUID) -> dict:
    """Return profile completion percentage and missing fields."""
    result = await db.execute(
        select(WorkerProfile)
        .options(selectinload(WorkerProfile.skills))
        .where(WorkerProfile.id == worker_id)
    )
    worker = result.scalar_one_or_none()
    if not worker:
        return {"percentage": 0.0, "missing_fields": ["profile not found"]}

    fields = {
        "experience_years": worker.experience_years is not None and worker.experience_years > 0,
        "daily_wage": worker.daily_wage is not None and worker.daily_wage > 0,
        "availability_status": worker.availability_status is not None,
        "skills": len(worker.skills) > 0,
    }

    filled = sum(1 for v in fields.values() if v)
    total = len(fields)
    missing = [k for k, v in fields.items() if not v]
    return {
        "percentage": round((filled / total) * 100, 1),
        "missing_fields": missing,
    }
