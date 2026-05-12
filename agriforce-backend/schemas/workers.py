from __future__ import annotations
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WorkerSkillOut(BaseModel):
    id: UUID
    name: str
    model_config = {"from_attributes": True}


class WorkerProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    experience_years: int
    daily_wage: float
    availability_status: str
    is_migrant: bool
    skills: list[WorkerSkillOut] = []

    model_config = {"from_attributes": True}


class RecommendedWorkerOut(BaseModel):
    id: UUID
    name: Optional[str]
    skills: list[str]
    distance: Optional[float]
    dailyWage: float
    experience_years: int
    availability_status: str


class ProfileCompletionOut(BaseModel):
    percentage: float
    missing_fields: list[str]


class EarningsDataPoint(BaseModel):
    month: str
    amount: float


class EarningsOut(BaseModel):
    labels: list[str]
    earnings: list[float]
