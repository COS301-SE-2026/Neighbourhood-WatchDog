from fastapi import HTTPException
from sqlalchemy import select
from app.schemas.audit_log import AuditLogScheme
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.database import DbSession
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

MOCK_IP_ADDRESS = "196.168.10.1"

async def create_audit_log_item(audit_log_details: AuditLogScheme, db: DbSession) -> None:
    if not db:
        raise HTTPException(500, "No database session. Could not create audit log item.")
    if not audit_log_details:
        raise HTTPException(500, "No audit log details provided. Could not create audit log item.")

    try:
        new_audit_log_item = AuditLog(
            id = uuid4,
            user_id = audit_log_details.user_id,
            action = audit_log_details.action,
            target_entity_type = audit_log_details.target_entity_type,
            target_entity_id = audit_log_details.target_entity_id,
            ip_address = audit_log_details.ip_address | MOCK_IP_ADDRESS,
            timestamp = audit_log_details,
            extra_metadata = audit_log_details.extra_metadata
        )

        db.add(new_audit_log_item)
        db.commit
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to add audit log item.")