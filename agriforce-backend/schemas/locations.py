from __future__ import annotations
from uuid import UUID

from pydantic import BaseModel


class StateOut(BaseModel):
    id: UUID
    name: str
    model_config = {"from_attributes": True}


class DistrictOut(BaseModel):
    id: UUID
    name: str
    state_id: UUID
    model_config = {"from_attributes": True}


class TalukOut(BaseModel):
    id: UUID
    name: str
    district_id: UUID
    model_config = {"from_attributes": True}
