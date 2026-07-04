from fastapi import APIRouter, Depends, Query
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.schemas.audit_log import GetAuditLogsRes, PaginatedResponse
from app.services.audit_service import get_audit_logs_handler

PAGE = 1
SIZE = 30

router = APIRouter(prefix="/audit", tags=["properties"])

@router.get("/get-audit-logs", response_model=PaginatedResponse[GetAuditLogsRes])
async def get_audit_logs(
    db: DbSession,
    claims: dict = Depends(get_current_user),
    page: int = Query(PAGE, ge=1, description="Page number"),
    size: int = Query(SIZE, ge=1, le=100, description="Items per page"),
):
    """Retrieves the all audit logs and returns them in a list."""
    
    return await get_audit_logs_handler(
        db,
        claims,
        page,
        size
    )