import enum
import uuid

from sqlalchemy import (Column, ForeignKey, Text, Enum, text)
from sqlalchemy.dialects.postgresql import (UUID, TIMESTAMPTZ, INET, JSONB)
from sqlalchemy.orm import relationship
from db.base import Base

class AuditAction(str, enum.Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    REGISTER_CAMERA = "REGISTER CAMERA"
    DELETE_CAMERA = "DELETE CAMERA"
    UPDTAE_ZONE_CONFIG = "UPDATE ZONE CONFIG"
    UPDTAE_THRESHOLD = "UPDATE THRESHOLD"
    ACKNOWLEDGE_ALERT = "ACKNOWLEDGE_ALERT"
    RESOLVE_ALERT = "RESOLVE ALERT"
    VIEW_FOOTAGE = "VIEW FOOTAGE"
    CREATE_NEIGHBOURHOOD = "CREATE NEIGHBOURHOOD"
    JOIN_NEIGHBOURHOOD = "JOIN NEIGHBOURHOOD"
    UPDATE_RETENTION_POLICY = "UPDATE RETENTION POLICY"
    REGISTER_ACCOUNT = "REGISTER ACCOUNT"
    UPDATE_CAMERA_VISIBILITY = "UPDATE CAMERA VISIBILITY"
    CONFIGURE_ALERT_THRESHOLD = "CONFIGURE ALERT THRESHOLD"

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(Enum(AuditAction, name="audit_action"), nullable=False)
    target_entity_type = Column(Text, nullable=True)
    target_entity_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(INET, nullable=False)
    timestamp = Column(TIMESTAMPTZ, nullable=False, server_default=text("now()"))
    metadata = Column(JSONB, nullable=True)
    extra_metadata = Column("metadata", JSONB, nullable=True)


    user = relationship("User", back_populates="audit_logs")


