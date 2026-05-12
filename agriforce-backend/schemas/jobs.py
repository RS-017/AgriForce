from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class JobPostCreate(BaseModel):
    crop_type_id: UUID
    district: str
    taluk: Optional[str] = None
    workers_required: int
    start_date: date
    end_date: date
    daily_wage_offered: float
    skill_ids: list[UUID] = []
    notes: Optional[str] = None


class JobPostOut(BaseModel):
    id: UUID
    farmer_id: UUID
    crop_type_id: UUID
    district: str
    taluk: Optional[str]
    workers_required: int
    start_date: date
    end_date: date
    daily_wage_offered: float
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TrainRequest(BaseModel):
    district: str
    crop_type: str
    historical_data: list[dict] = []
