from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional

from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.auth.rbac import require_role
from app.schemas.audit_log import GetAuditLogsRes, AuditAction
from app.services.audit_service import get_audit_logs_handler

PAGE = 1
SIZE = 30

router = APIRouter(prefix="/audit", tags=["properties"])

@router.get("/get-audit-logs")
async def get_audit_logs(
    db: DbSession,
    claims: dict = Depends(get_current_user),
    page: int = Query(PAGE, ge=1, description="Page number"),
    size: int = Query(SIZE, ge=1, le=100, description="Items per page"),
    search_term: Optional[str] = Query(None, description="Free-text search"),
    action: Optional[AuditAction] = Query(None, description="Filter by action"),
    start_date: Optional[datetime] = Query(None, description="Logs on/after this date"),
    end_date: Optional[datetime] = Query(None, description="Logs on/before this date"),
    target_entity_type: Optional[str] = Query(None, description="Filter by target entity type"),
    sort_order: Optional[str] = Query(None, description="ASC or DESC"),
):
    """Retrieves the all audit logs and returns them in a list."""
    require_role(claims, ["SYSTEM_ADMIN"])
    
    return await get_audit_logs_handler(
        search_term=search_term,
        action=action,
        start_date=start_date,
        end_date=end_date,
        target_entity_type=target_entity_type,
        sort_order=sort_order,
        db=db,
        page=page,
        size=size
    )