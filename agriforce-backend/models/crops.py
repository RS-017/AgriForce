import uuid
import enum

from sqlalchemy import Column, Date, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Season(str, enum.Enum):
    KHARIF = "KHARIF"
    RABI = "RABI"
    ZAID = "ZAID"


class Crop(Base):
    __tablename__ = "crops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    peak_sowing_start = Column(Date)
    peak_sowing_end = Column(Date)
    peak_harvest_start = Column(Date)
    peak_harvest_end = Column(Date)
    season = Column(Enum(Season))

    subsidy_schemes = relationship(
        "SubsidyScheme", secondary="subsidy_crop_links", back_populates="crops"
    )
