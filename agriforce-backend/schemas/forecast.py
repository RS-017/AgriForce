from __future__ import annotations
from datetime import date
from typing import Optional

from pydantic import BaseModel


class ForecastDataPoint(BaseModel):
    date: str  # ISO date string e.g. "2026-06-01"
    predicted: float
    lower_80: float
    upper_80: float
    lower_95: float
    upper_95: float


class ForecastOut(BaseModel):
    district: str
    crop_type: str
    labels: list[str]
    demand: list[float]
    confidence_lower_80: list[float]
    confidence_upper_80: list[float]
    confidence_lower_95: list[float]
    confidence_upper_95: list[float]
    data_points: list[ForecastDataPoint]
