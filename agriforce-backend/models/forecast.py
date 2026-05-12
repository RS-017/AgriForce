import uuid

from sqlalchemy import Column, Date, Float, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class LabourDemandForecast(Base):
    __tablename__ = "labour_demand_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district = Column(String(100), nullable=False, index=True)
    crop_type_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    forecast_date = Column(Date, nullable=False, index=True)
    predicted_demand_score = Column(Float, nullable=False)
    confidence_lower_80 = Column(Float)
    confidence_upper_80 = Column(Float)
    confidence_lower_95 = Column(Float)
    confidence_upper_95 = Column(Float)
    model_version = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    crop = relationship("Crop")
