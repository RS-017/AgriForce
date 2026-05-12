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
    dailyRate: Optional[float] = None  # camelCase alias for frontend
    district: str
    availability_status: str
    available: Optional[bool] = None  # derived: True when AVAILABLE
    images: list[str] = []
    image: Optional[str] = None  # first image URL for card display

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        # Derive convenience fields
        instance.available = (instance.availability_status == "AVAILABLE")
        instance.dailyRate = instance.daily_rate
        instance.image = instance.images[0] if instance.images else None
        return instance


class RentalBookingOut(BaseModel):
    id: UUID
    equipment_id: UUID
    farmer_id: UUID
    start_date: date
    end_date: date
    total_cost: float
    status: str

    model_config = {"from_attributes": True}
