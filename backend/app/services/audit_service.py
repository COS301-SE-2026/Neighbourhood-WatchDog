from fastapi import HTTPException
from pydantic import Json
from sqlalchemy import select
from app.models.audit_log import AuditAction
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.database import DbSession
from sqlalchemy.exc import IntegrityError
from uuid import uuid4, UUID
from datetime import datetime

async def create_audit_log_item(user_id: UUID, action: AuditAction, target_entity_type: str, target_entity_id: UUID, old_values: dict, new_values: dict, db: DbSession) -> AuditLog:
    """Receives an AuditLogScheme object and adds the audit log to the database."""
    if not db:
        raise HTTPException(500, "Could not create audit log item. No database session.")
    
    if not user_id:
        raise HTTPException(500, "Could not create audit log item. No user id provided.")

    if not target_entity_type:
        raise HTTPException(500, "Could not create audit log item. No target entity type provided.")
    
    if not target_entity_id:
        raise HTTPException(500, "Could not create audit log item. No target entity id provided.")
    
    if not action:
        raise HTTPException(500, "Could not create audit log item. No action provided.")

    if action == AuditAction.DELETE:
        new_values = None

        if not old_values: # old must exist
            raise HTTPException(500, "Could not create audit log item. No old value provided.")
   
    elif action == AuditAction.UPDATE:
        if not old_values or not new_values:
            raise HTTPException(500, "Could not create audit log item. Either old or new values were not provided.")
   
    elif action == AuditAction.CREATE:
        old_values = None

        if not new_values:
            raise HTTPException(500, "Could not create audit log item. New values were not provided.")

    if old_values == new_values:
        raise HTTPException(500, "Could not create audit log item. Old values and new values are the same.")

    try:
        #TODO: check that id in table actually exists

        #TODO: check the cases around the action and what is being done

        new_audit_log_item = AuditLog(
            id = uuid4(),
            user_id = user_id,
            action = action,
            target_entity_type = target_entity_type,
            target_entity_id = target_entity_id,
            new_values = new_values,
            old_values = old_values 
        )

        db.add(new_audit_log_item)
        db.commit()
        db.refresh(new_audit_log_item)

        return new_audit_log_item
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Could not create audit log item. Failed to add audit log item.")
    
async def get_audits_handler():
    # include pagination here
    pass