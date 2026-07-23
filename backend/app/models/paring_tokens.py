from app.core.database import Base
from sqlalchemy import Column, text, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import relationship
from uuid import UUID

class PairingToken(Base):
    __tablename__ = "pairing_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    token = Column(String, nullable=False, unique=True, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now() + interval '10 minutes'"))
    used_at = Column(TIMESTAMP(timezone=True), nullable=True)

    property = relationship("Property", foreign_keys=[property_id])
