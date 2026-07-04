from fastapi import APIRouter, Depends, Query
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.auth.rbac import require_role
from sqlalchemy import select, func
from app.models.audit_log import AuditLog
from app.schemas.audit_log import GetAuditLogsRes, PaginatedResponse

router = APIRouter(prefix="/audit", tags=["properties"])

@router.post("get-audit-logs" ,response_model=PaginatedResponse[GetAuditLogsRes])
async def get_audit_logs(
    db: DbSession,
    claims: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Retrieves the all audit logs and returns them in a list."""

    require_role(claims, ['SYSTEM_ADMIN'])
    offset = (page - 1) * size

    total_count = db.scalar(select(func.count()).select_from(AuditLog))
    stmt = select(AuditLog).offset(offset).limit(size).order_by(AuditLog.id)
    audit_logs = db.scalars(stmt).all()
    
    return PaginatedResponse(
        total=total_count,
        page=page,
        size=size,
        results=audit_logs
    )