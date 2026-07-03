from fastapi import HTTPException
from pydantic import Json, IPvAnyAddress
from sqlalchemy import select
from app.models.audit_log import AuditAction
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.database import DbSession
from sqlalchemy.exc import IntegrityError
from uuid import uuid4, UUID
from datetime import datetime

MOCK_IP_ADDRESS = "196.168.10.1"

async def create_audit_log_item(user_id: UUID, action: AuditAction, target_entity_type: str, target_entity_id: UUID, ip_address: IPvAnyAddress, timestamp: datetime, extra_metadata, db: DbSession) -> AuditLog:
    """Receives an AuditLogScheme object and adds the audit log to the database."""
    if not db:
        raise HTTPException(500, "No database session. Could not create audit log item.")
    
    if not user_id:
        raise HTTPException(500, "No user id provided. Could not create audit log item.")
    
    if not action:
        raise HTTPException(500, "No action provided. Could not create audit log item.")

    if not target_entity_type:
        raise HTTPException(500, "No target entity type provided. Could not create audit log item.")
    
    if not target_entity_id:
        raise HTTPException(500, "No target entity id provided. Could not create audit log item.")
    
    if not ip_address:
        raise HTTPException(500, "No IP Address provided. Could not create audit log item.")
    
    if not extra_metadata:
        raise HTTPException(500, "No  provided. Could not create audit log item.")

    try:
        new_audit_log_item = AuditLog(
            id = uuid4,
            user_id = user_id,
            action = action,
            target_entity_type = target_entity_type,
            target_entity_id = target_entity_id,
            ip_address = ip_address | MOCK_IP_ADDRESS,
            timestamp = timestamp,
            extra_metadata = extra_metadata
        )

        db.add(new_audit_log_item)
        db.commit

        return new_audit_log_item
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to add audit log item.")