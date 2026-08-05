from app.core.database import Base
from sqlalchemy import Column, Index, text, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID


class EdgeAgentCredential(Base):
    __tablename__ = "edge_agents_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id", ondelete="CASCADE"), nullable=True)
    key_hash = Column(String, nullable=False, unique=True, index=True) #hashed api key value
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)


    property = relationship("Property", foreign_keys=[property_id])

    __table_args__ = (
        Index("ix_edge_agent_credentials_property_id", "property_id"),
    )
    