from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    jobId: UUID
    workerId: UUID


class ApplicationOut(BaseModel):
    id: UUID
    job_id: UUID
    worker_id: UUID
    status: str
    applied_at: Optional[datetime]
    jobTitle: Optional[str] = None
    farmerName: Optional[str] = None
    appliedDate: Optional[str] = None

    model_config = {"from_attributes": True}
