from fastapi import HTTPException, Depends, Query
from app.auth.dependencies import get_current_user
from app.models.audit_log import AuditAction
from app.models.audit_log import AuditLog
from app.core.database import DbSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from app.schemas.audit_log import GetAuditLogsRes, PaginatedResponse, AuditLogScheme
from uuid import uuid4, UUID
from fastapi.exceptions import ResponseValidationError

PAGE = 1
SIZE = 30

async def create_audit_log_item(
    user_id: UUID, 
    action: AuditAction, 
    target_entity_type: str,
    target_entity_id: UUID,
    old_values: dict,
    new_values: dict,
    db: DbSession
) -> AuditLog:
    """Receives an AuditLogScheme object and adds the audit log to the database."""
    if not db:
        raise HTTPException(400, "Could not create audit log item. No database session.")
    
    if not user_id:
        raise HTTPException(400, "Could not create audit log item. No user id provided.")

    if not target_entity_type:
        raise HTTPException(400, "Could not create audit log item. No target entity type provided.")
    
    if not target_entity_id:
        raise HTTPException(400, "Could not create audit log item. No target entity id provided.")
    
    if not action:
        raise HTTPException(400, "Could not create audit log item. No action provided.")

    if action == AuditAction.DELETE:
        new_values = None

        if not old_values: # old must exist
            raise HTTPException(400, "Could not create audit log item. No old value provided.")
   
    elif action == AuditAction.UPDATE:
        if not old_values or not new_values:
            raise HTTPException(400, "Could not create audit log item. Either old or new values were not provided.")
   
    elif action == AuditAction.CREATE:
        old_values = None

        if not new_values:
            raise HTTPException(400, "Could not create audit log item. New values were not provided.")

    if old_values == new_values:
        raise HTTPException(400, "Could not create audit log item. Old values and new values are the same.")

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
        raise HTTPException(400, "Could not create audit log item. Failed to add audit log item.")

async def get_audit_logs_handler(
    page: int,
    size: int,
    db: DbSession,
) -> GetAuditLogsRes:
    
    if not db:
        raise HTTPException(500, "No database.")

    offset = (page - 1) * size

    total_count = db.scalar(select(func.count()).select_from(AuditLog))

    if offset > total_count:
        raise HTTPException(422, "Request is beyond the total number of audit logs.")

    stmt = select(AuditLog).offset(offset).limit(size).order_by(AuditLog.id)
    audit_logs = db.scalars(stmt).all()

    results = [AuditLogScheme.model_validate(a) for a in audit_logs]
    
    paginated = PaginatedResponse[AuditLogScheme](
        total = total_count,
        page = page,
        size = size,
        results = results
    )
    output = GetAuditLogsRes(
        status=200,
        message="OK",
        data=paginated
    )

    return output