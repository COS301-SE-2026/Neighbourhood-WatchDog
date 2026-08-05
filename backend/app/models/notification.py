import uuid
from enum import Enum
from sqlalchemy import Column, Index, String, ForeignKey, text, TIMESTAMP, Enum as SAEnum
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
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alert.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(SAEnum(NotificationChannel, name="notification_channel"), nullable=False)
    status = Column(SAEnum(NotificationStatus, name="notification_status"), nullable=False)
    error_message = Column(String, nullable=True)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    alert = relationship("Alert", backref="notifications")
    user = relationship("User", backref="notifications")

    __table_args__ = (
        Index("ix_notification_alert_id", "alert_id"),
        Index("ix_notification_user_sent_at", "user_id", "sent_at"),
    )
    
    