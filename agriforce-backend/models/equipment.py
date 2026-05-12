import uuid
import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, String, Text, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class EquipmentStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    MAINTENANCE = "MAINTENANCE"


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(Text)
    daily_rate = Column(Float, nullable=False)
    district = Column(String(100), nullable=False)
    availability_status = Column(Enum(EquipmentStatus), default=EquipmentStatus.AVAILABLE)
    images = Column(ARRAY(Text), default=[])

    provider = relationship("User")
    bookings = relationship("RentalBooking", back_populates="equipment", cascade="all, delete-orphan")


class RentalBooking(Base):
    __tablename__ = "rental_bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_cost = Column(Float, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    equipment = relationship("Equipment", back_populates="bookings")
    farmer = relationship("FarmerProfile", back_populates="rental_bookings")
