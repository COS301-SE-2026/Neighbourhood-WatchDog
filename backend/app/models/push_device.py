"""Table that keeps track of a user's devices which receive
push notifications. It is linked to the users table and keeps track of the device token"""

from app.core.database import Base
from sqlalchemy import Column, ForeignKey, String, text,TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class PushDevice(Base):
    __tablename__ = "push_device"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_token = Column(String,nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    user = relationship("User", foreign_keys=[user_id], back_populates="push_devices")