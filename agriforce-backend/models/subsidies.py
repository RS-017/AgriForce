import uuid

from sqlalchemy import (
    Boolean, Column, Date, Float, ForeignKey, String, Text, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class SubsidyScheme(Base):
    __tablename__ = "subsidy_schemes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    ministry = Column(String(200))
    eligible_land_size_max = Column(Float)
    eligible_regions = Column(ARRAY(Text), default=[])
    deadline = Column(Date)
    portal_url = Column(Text)
    description = Column(Text)

    crops = relationship("Crop", secondary="subsidy_crop_links", back_populates="subsidy_schemes")
    eligibility_checks = relationship("EligibilityCheck", back_populates="scheme")


class SubsidyCropLink(Base):
    __tablename__ = "subsidy_crop_links"

    scheme_id = Column(UUID(as_uuid=True), ForeignKey("subsidy_schemes.id", ondelete="CASCADE"), primary_key=True)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id", ondelete="CASCADE"), primary_key=True)


class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("subsidy_schemes.id", ondelete="CASCADE"), nullable=False)
    is_eligible = Column(Boolean, nullable=False)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer = relationship("FarmerProfile", back_populates="eligibility_checks")
    scheme = relationship("SubsidyScheme", back_populates="eligibility_checks")
