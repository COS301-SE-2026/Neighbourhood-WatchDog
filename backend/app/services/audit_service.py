from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import String, select, func, or_, cast
from uuid import uuid4, UUID
from datetime import datetime

from app.models.audit_log import AuditAction
from app.models.audit_log import AuditLog
from app.core.database import DbSession
from app.schemas.audit_log import GetAuditLogsRes, PaginatedResponse, AuditLogScheme

PAGE = 1
SIZE = 30

def create_audit_log_item(
    user_id: UUID, 
    action: AuditAction, 
    target_entity_type: str,
    target_entity_id: UUID,
    old_values: dict,
    new_values: dict,
    db: DbSession
) -> AuditLog:
    """Receives an AuditLogScheme object and adds the audit log to the database."""
    _validate_required_create_fields(db, user_id, target_entity_type, target_entity_id, action)
    old_values, new_values = _validate_action_values(action, old_values, new_values)
    
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

def _validate_required_create_fields(db, user_id, target_entity_type, target_entity_id, action):
    required = {
        "database_session": db,
        "user id": user_id,
        "target entity type": target_entity_type,
        "target entity id": target_entity_id,
        "action": action,
    }

    for name, value in required.items():
        if not value:
            raise HTTPException(400, f"Could not create audit log item. No {name} provided.")
        
def _validate_action_values(action, old_values, new_values):
    if action == AuditAction.DELETE:
        if not old_values: # old must exist
            raise HTTPException(400, "Could not create audit log item. No old value provided.")
        return old_values, None
    
    elif action == AuditAction.UPDATE:
        if not old_values or not new_values:
            raise HTTPException(400, "Could not create audit log item. Either old or new values were not provided.")
        if old_values == new_values:
            raise HTTPException(400, "Could not create audit log item. Old values and new values are the same.")
        return old_values, new_values

    elif action == AuditAction.CREATE:
        if not new_values:
            raise HTTPException(400, "Could not create audit log item. New values were not provided.")
        return None, new_values
    
    return old_values, new_values


async def get_audit_logs_handler(
    page: int,
    size: int,
    db: DbSession,
    search_term: str = None,
    action: AuditAction = None,
    start_date: datetime = None,
    end_date: datetime = None,
    sort_order: str = None,
) -> GetAuditLogsRes:
    #TODO: consider returning the username as well
    if not db:
        raise HTTPException(500, "No database.")

    if page < 1:
        raise HTTPException(422, "page must be >= 1.")
    if size < 1:
        raise HTTPException(422, "size must be >= 1.")

    stmt = select(AuditLog)

    # Filters
    if search_term:
        search_cols = [AuditLog.id, AuditLog.action, AuditLog.target_entity_type, AuditLog.target_entity_id]
        conditions = [
            cast(col, String).ilike(f"%{search_term}%") #non case sensitive search on any str field
            for col in search_cols
        ]
        if conditions:
            stmt = stmt.where(or_(*conditions))

    if action:
        stmt = stmt.where(AuditLog.action == action)

    if start_date:
        stmt = stmt.where(AuditLog.timestamp >= start_date)

    if end_date:
        stmt = stmt.where(AuditLog.timestamp <= end_date)
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.scalar(count_stmt)

    offset = (page - 1) * size
    if total_count and offset >= total_count:
        raise HTTPException(422, "Request is beyond the total number of audit logs.")

    if sort_order and sort_order == "ASC":
        stmt = stmt.order_by(AuditLog.timestamp.asc())
    elif sort_order and sort_order == "DESC":
        stmt = stmt.order_by(AuditLog.timestamp.desc())
    else: 
        stmt = stmt.order_by(AuditLog.id.desc())

    stmt = stmt.offset(offset).limit(size)
    
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

def _validate_pagination(page: int, size: int):
    if page < 1:
        raise HTTPException(422, "page must be >= 1")
    if size < 1:
        raise HTTPException(422, "size must be >= 1")
    
