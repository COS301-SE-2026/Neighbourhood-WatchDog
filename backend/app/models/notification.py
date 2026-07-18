import uuid
from enum import Enum
from sqlalchemy import Column, String, ForeignKey, text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class NotificationChannel(str, Enum):
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"

class NotificationStatus(str, Enum):
    SENT = "SENT"
    FAILED = "FAILED"

class Notification(Base):
    __tablename__ = "notification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alert.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    channel = Column(String, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    alert = relationship("Alert", backref="notifications")
    user = relationship("User", backref="notifications")
    
    