from pydantic import BaseModel, Json
from typing import List, Generic, TypeVar
from app.schemas.property import NonEmptyString
from uuid import UUID
from app.models.audit_log import AuditAction
from datetime import datetime


class GetAuditLogsReq(BaseModel):
    id: UUID | None = None
    user_id: UUID | None = None
    target_entity_type: NonEmptyString | None = None
    target_entity_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

class AuditLogScheme(BaseModel):
    id: UUID
    user_id: UUID
    action: AuditAction
    target_entity_type: NonEmptyString | None = None
    target_entity_id: UUID | None = None
    timestamp: datetime
    old_values: Json | None = None
    new_values: Json | None = None

class GetAuditLogsRes(BaseModel):
    status: int
    message: str | None = None
    data: list[AuditLogScheme] = None

