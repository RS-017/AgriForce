from __future__ import annotations
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RentalBookingCreate(BaseModel):
    equipmentId: UUID
    startDate: date
    endDate: date


class EquipmentOut(BaseModel):
    id: UUID
    name: str
    type: str
    description: Optional[str]
    daily_rate: float
    district: str
    availability_status: str
    images: list[str] = []

    model_config = {"from_attributes": True}


class RentalBookingOut(BaseModel):
    id: UUID
    equipment_id: UUID
    farmer_id: UUID
    start_date: date
    end_date: date
    total_cost: float
    status: str

    model_config = {"from_attributes": True}
