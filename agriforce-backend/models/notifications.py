import uuid
import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class NotificationType(str, enum.Enum):
    JOB_ALERT = "JOB_ALERT"
    APPLICATION_UPDATE = "APPLICATION_UPDATE"
    SUBSIDY_ALERT = "SUBSIDY_ALERT"
    SYSTEM = "SYSTEM"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType, name="notification_type"), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
