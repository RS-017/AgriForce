"""routers/auth.py — Authentication endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

import core.otp as otp_service
from core.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from core.rate_limit import limiter
from database import get_db
from models.users import (
    FarmerProfile, LandType, User, UserRole, WorkerProfile, Skill, WorkerSkill, AvailabilityStatus
)
from schemas.auth import OTPRequest, OTPVerify, TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def validateRegistrationForm(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register user + create role-specific profile."""
    # Check uniqueness
    existing = await db.execute(
        select(User).where(or_(User.phone == body.phone, User.email == body.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone or email already registered")

    role = UserRole(body.role)
    hashed = hash_password(body.password)

    user = User(
        id=uuid.uuid4(),
        phone=body.phone,
        email=body.email,
        hashed_password=hashed,
        role=role,
    )
    db.add(user)
    await db.flush()  # get user.id before profile insert

    if role == UserRole.FARMER:
        profile = FarmerProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            farm_size=body.farmSize,
            primary_crop=body.primaryCrop,
            district=body.district,
            taluk=body.taluk,
            land_type=LandType(body.landType) if body.landType else None,
        )
        db.add(profile)

    elif role == UserRole.WORKER:
        profile = WorkerProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            experience_years=body.experienceYears or 0,
            daily_wage=body.expectedWage or 0.0,
            availability_status=AvailabilityStatus.AVAILABLE,
        )
        db.add(profile)
        await db.flush()

        # Attach skills
        for skill_name in (body.skills or []):
            skill_result = await db.execute(select(Skill).where(Skill.name == skill_name))
            skill = skill_result.scalar_one_or_none()
            if not skill:
                skill = Skill(id=uuid.uuid4(), name=skill_name)
                db.add(skill)
                await db.flush()
            db.add(WorkerSkill(worker_id=profile.id, skill_id=skill.id))

    await db.commit()

    access_token = create_access_token({"sub": str(user.id), "role": role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, role=role.value)


@router.post("/login", response_model=TokenResponse)
async def validateLoginForm(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    result = await db.execute(
        select(User).where(or_(User.phone == body.phone, User.email == body.phone))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role.value,
        token=access_token,  # For frontend compatibility
    )


@router.post("/request-otp")
@limiter.limit("3/10minutes")
async def requestOTP(body: OTPRequest, request: Request):
    """Generate a 6-digit OTP. In development the code is returned as 'dev_otp'."""
    result = await otp_service.requestOTP(body.phone)
    # dev_otp is present so callers can see the code without a real SMS provider
    return {"status": result.get("status", "pending"), "dev_otp": result.get("dev_otp")}


@router.post("/verify-otp")
async def verifyOTP(body: OTPVerify, db: AsyncSession = Depends(get_db)):
    """Verify OTP code and mark user as verified."""
    approved = await otp_service.verifyOTP(body.phone, body.otp)
    if not approved:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()
    if user:
        user.is_verified = True
        await db.commit()

    return {"verified": True}


@router.post("/logout")
async def logoutUser(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Blacklist the current access token."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        blacklist_token(token)
    return {"message": "logged out"}
