from pydantic import BaseModel, Json, IPvAnyAddress, IPvAnyInterface
from app.schemas.property import NonEmptyString
from uuid import UUID
from audit_log import AuditAction
from datetime import datetime

class AuditScheme(BaseModel):
    user_id: UUID
    action: AuditAction
    target_entity_type: NonEmptyString | None = None
    target_entity_id: UUID | None = None
    ip_address: IPvAnyAddress
    timestamp: datetime
    extra_metadata: Json | None = None