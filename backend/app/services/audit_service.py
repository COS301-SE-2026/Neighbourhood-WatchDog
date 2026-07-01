from fastapi import HTTPException
from app.schemas.audit_log import AuditLogScheme
from app.core.database import DbSession

MOCK_IP_ADDRESS = "196.168.10.1"

async def create_audit_log(audit_log: AuditLogScheme, db: DbSession, claims: dict) -> None:
    if not db:
        raise HTTPException(500, "No database session")
    if not claims:
        raise HTTPException(401, "Not authenticated")
    