from app.core.database import Base
from sqlalchemy import Column, text, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import relationship
from uuid import UUID

class EdgeAgentCredential(Base):
    __tablename__ = "edge_agents_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id"), nullable=True)
    key_hash = Column(String, nullable=False, unique=True, index=True) #ha
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)


    property = relationship("Property", foreign_keys=[property_id])
    