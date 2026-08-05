from app.core.database import Base
from sqlalchemy import Column, text, ForeignKey, TIMESTAMP, String, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

class PairingToken(Base):
    __tablename__ = "pairing_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    token = Column(String, nullable=False, unique=True, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id"), ondelete="CASCADE", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now() + interval '10 minutes'")) # expires in 10 minutes
    used_at = Column(TIMESTAMP(timezone=True), nullable=True)

    property = relationship("Property", foreign_keys=[property_id])

    __table_args__ = (
        CheckConstraint("created_at < expires_at", "created_before_expires"),
        CheckConstraint("used_at < expires_at", "expires_after_used")
    )