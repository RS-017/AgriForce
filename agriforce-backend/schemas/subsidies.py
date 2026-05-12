from __future__ import annotations
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SubsidySchemeOut(BaseModel):
    id: UUID
    name: str
    ministry: Optional[str]
    eligible_land_size_max: Optional[float]
    eligible_regions: list[str] = []
    deadline: Optional[date]
    portal_url: Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


class SubsidyAlertOut(BaseModel):
    id: UUID
    schemeName: str
    deadlineDays: int


class EligibilityCriterion(BaseModel):
    name: str
    met: bool


class EligibilityRequest(BaseModel):
    farmerProfile: dict
    schemeId: UUID


class EligibilityResult(BaseModel):
    is_eligible: bool
    criteria: list[EligibilityCriterion]
