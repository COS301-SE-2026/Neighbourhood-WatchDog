from enum import Enum as PyEnum
import uuid

from sqlalchemy import Column, ForeignKey, Text, Enum, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditAction(str, PyEnum):
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(Enum(AuditAction), nullable=False)
    target_entity_type = Column(Text, nullable=True)
    target_entity_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="audit_logs")



