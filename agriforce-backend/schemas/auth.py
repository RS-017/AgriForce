from __future__ import annotations
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    password: str
    name: Optional[str] = None
    role: str  # "FARMER" | "WORKER" | "EQUIPMENT_PROVIDER"
    # Farmer extras
    farmSize: Optional[float] = None
    primaryCrop: Optional[str] = None
    district: Optional[str] = None
    taluk: Optional[str] = None
    landType: Optional[str] = None
    # Worker extras
    experienceYears: Optional[int] = None
    expectedWage: Optional[float] = None
    skills: Optional[list[str]] = []
    # Provider extras
    businessName: Optional[str] = None
    equipmentTypes: Optional[str] = None
    providerDistrict: Optional[str] = None

    # Silently ignore extra form fields like 'confirmPassword'
    model_config = {"extra": "ignore"}


class UserLogin(BaseModel):
    phone: str  # phone OR email (frontend sends as 'phone')
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    token: Optional[str] = None  # alias for access_token (frontend compat)


class UserResponse(BaseModel):
    id: UUID
    phone: str
    email: Optional[str]
    role: str
    is_verified: bool
    is_active: bool

    model_config = {"from_attributes": True}


class OTPRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: str
