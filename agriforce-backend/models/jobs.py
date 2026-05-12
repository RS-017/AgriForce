import uuid
import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey,
    Integer, String, UniqueConstraint, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class JobStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FILLED = "FILLED"


class ApplicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class JobPost(Base):
    __tablename__ = "job_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False)
    crop_type_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    district = Column(String(100), nullable=False)
    taluk = Column(String(100))
    workers_required = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    daily_wage_offered = Column(Float, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.OPEN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer = relationship("FarmerProfile", back_populates="job_posts")
    crop = relationship("Crop")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "worker_id", name="uq_application"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobPost", back_populates="applications")
    worker = relationship("WorkerProfile", back_populates="applications")
