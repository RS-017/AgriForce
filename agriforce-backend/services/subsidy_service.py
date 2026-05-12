"""subsidy_service.py — Eligibility checking business logic."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.subsidies import SubsidyScheme


async def checkSubsidyEligibility(
    db: AsyncSession, farmer_profile: dict, scheme_id: UUID
) -> dict:
    """
    Cross-check farmer profile against scheme eligibility rules.
    Returns per-criterion pass/fail breakdown.
    """
    result = await db.execute(
        select(SubsidyScheme)
        .options(selectinload(SubsidyScheme.crops))
        .where(SubsidyScheme.id == scheme_id)
    )
    scheme = result.scalar_one_or_none()
    if not scheme:
        return {"is_eligible": False, "criteria": [{"name": "Scheme not found", "met": False}]}

    criteria = []

    # 1. Land size check
    farm_size = float(farmer_profile.get("farm_size") or farmer_profile.get("farmSize") or 0)
    if scheme.eligible_land_size_max:
        passed = farm_size <= scheme.eligible_land_size_max
        criteria.append(
            {"name": f"Farm size ≤ {scheme.eligible_land_size_max} acres", "met": passed}
        )

    # 2. Region check
    farmer_district = (farmer_profile.get("district") or "").lower()
    if scheme.eligible_regions:
        passed = any(
            farmer_district in r.lower() for r in scheme.eligible_regions
        )
        criteria.append({"name": "Region eligibility", "met": passed})

    # 3. Crop type check
    farmer_crop = (farmer_profile.get("primary_crop") or farmer_profile.get("primaryCrop") or "").lower()
    scheme_crops = [c.name.lower() for c in scheme.crops]
    if scheme_crops:
        passed = farmer_crop in scheme_crops or not scheme_crops
        criteria.append({"name": f"Crop eligibility ({farmer_crop})", "met": passed})

    is_eligible = all(c["met"] for c in criteria) if criteria else True

    return {"is_eligible": is_eligible, "criteria": criteria}
