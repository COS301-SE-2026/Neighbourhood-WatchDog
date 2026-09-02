from enum import Enum
import uuid

from sqlalchemy import Column, ForeignKey, Index, text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditAction(str, Enum):
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"

class TargetEntity(str, Enum):
    ALERT = "ALERT"
    CAMERADETECTIONZONE = "CAMERADETECTIONZONE"
    CAMERA = "CAMERA"
    EDGEAGENTCREDENTIALS = "EDGEAGENTCREDENTIALS"
    NEIGHBOURHOODJOINREQUEST = "NEIGHBOURHOODJOINREQUEST"
    NEIGHBOURHOOD = "NEIGHBOURHOOD"
    NEIGHBOURHOODUSER = "NEIGHBOURHOODUSER"
    NOTIFICATION = "NOTIFICATION"
    PAIRINGTOKEN = "PAIRINGTOKEN"
    PROPERTYUSER = "PROPERTYUSER"
    PROPERTY = "PROPERTY"
    RETENTIONPOLICY = "RETENTIONPOLICY"
    RISKSCOREHISTORY = "RISKSCOREHISTORY"
    RISKTHRESHOLDCONFIG = "RISKTHRESHOLDCONFIG"
    USER = "USER"
    ZONE = "ZONE"

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(SAEnum(AuditAction), nullable=False)
    target_entity_type = Column(SAEnum(TargetEntity), nullable=True)
    target_entity_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_log_user_action_timestamp", "user_id", "action", "timestamp"),
        Index("ix_audit_log_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_log_entity", "target_entity_type", "target_entity_id", "timestamp"),
    )