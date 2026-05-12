import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class UserRole(str, enum.Enum):
    FARMER = "FARMER"
    WORKER = "WORKER"
    EQUIPMENT_PROVIDER = "EQUIPMENT_PROVIDER"
    ADMIN = "ADMIN"


class LandType(str, enum.Enum):
    IRRIGATED = "IRRIGATED"
    RAINFED = "RAINFED"
    DRY = "DRY"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    MIGRATED = "MIGRATED"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(Text, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer_profile = relationship(
        "FarmerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    worker_profile = relationship(
        "WorkerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    farm_size = Column(Float)
    primary_crop = Column(String(100))
    district = Column(String(100))
    taluk = Column(String(100))
    land_type = Column(Enum(LandType))

    user = relationship("User", back_populates="farmer_profile")
    job_posts = relationship("JobPost", back_populates="farmer", cascade="all, delete-orphan")
    rental_bookings = relationship("RentalBooking", back_populates="farmer")
    eligibility_checks = relationship("EligibilityCheck", back_populates="farmer")


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    experience_years = Column(Integer, default=0)
    daily_wage = Column(Float, default=0.0)
    availability_status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.AVAILABLE)
    is_migrant = Column(Boolean, default=False)

    user = relationship("User", back_populates="worker_profile", foreign_keys=[user_id])
    skills = relationship("Skill", secondary="worker_skills", back_populates="workers")
    applications = relationship("Application", back_populates="worker", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)

    workers = relationship("WorkerProfile", secondary="worker_skills", back_populates="skills")


class WorkerSkill(Base):
    __tablename__ = "worker_skills"
    __table_args__ = (UniqueConstraint("worker_id", "skill_id"),)

    worker_id = Column(UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
