from pydantic import BaseModel, Json, IPvAnyAddress, IPvAnyInterface
from app.schemas.property import NonEmptyString
from uuid import UUID
from app.models.audit_log import AuditAction
from datetime import datetime

class AuditLogScheme(BaseModel):
    id: UUID
    user_id: UUID
    action: AuditAction
    target_entity_type: NonEmptyString | None = None
    target_entity_id: UUID | None = None
    ip_address: IPvAnyAddress
    timestamp: datetime
    old_values: Json | None = None
    new_values: Json | None = None

class GetAuditLogsRes(BaseModel):
    status: int
    message: str | None = None
    data: list[AuditLogScheme] = None