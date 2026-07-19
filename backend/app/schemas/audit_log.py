from pydantic import BaseModel, ConfigDict
from typing import Any, List, Generic, TypeVar
from app.schemas.property import NonEmptyString
from uuid import UUID
from app.models.audit_log import AuditAction
from datetime import datetime

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    size: int
    results: List[T]

class AuditLogScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    action: AuditAction
    target_entity_type: NonEmptyString | None = None
    target_entity_id: UUID | None = None
    timestamp: datetime
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None

class GetAuditLogsRes(BaseModel):
    status: int
    message: str | None = None
    data: PaginatedResponse[AuditLogScheme] 