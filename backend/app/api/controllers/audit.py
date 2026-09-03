from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Query

from app.auth.authorization import SystemAdminClaims
from app.core.database import DbSession
from app.schemas.audit_log import AuditAction, GetAuditLogsRes
from app.services.audit_service import get_audit_logs_handler

PAGE = 1
SIZE = 30

router = APIRouter(prefix="/audit", tags=["properties"])

@router.get(
    "/get-audit-logs",
    response_model=GetAuditLogsRes,
    summary="Retrieve audit logs",
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid pagination parameters or requested page exceeds available audit logs"},
        500: {"description": "No database session"},
    },
)
async def get_audit_logs(
    db: DbSession,
    claims: SystemAdminClaims,
    page: Annotated[int, Query(ge=1, description="Page number")] = PAGE,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = SIZE, 
    search_term: Annotated[Optional[str], Query(description="Free-text search")] = None, 
    action: Annotated[Optional[AuditAction], Query(description="Filter by action")] = None,
    start_date: Annotated[Optional[datetime], Query(description="Logs on/after this date")] = None,
    target_entity_type: Annotated[Optional[str], Query(description="Filter by target entity type")] = None,
    end_date: Annotated[Optional[datetime], Query(description="Logs on/before this date")] = None,
    sort_order: Annotated[Optional[str], Query(description="ASC or DESC")] = None, 
):
    """Retrieves the all audit logs and returns them in a list."""
    
    
    return await get_audit_logs_handler(
        search_term=search_term,
        action=action,
        start_date=start_date,
        end_date=end_date,
        sort_order=sort_order,
        db=db,
        page=page,
        size=size
    )