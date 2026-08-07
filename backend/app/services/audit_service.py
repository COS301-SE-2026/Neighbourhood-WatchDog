from fastapi import HTTPException
from sqlalchemy import String, select, func, or_, cast
from uuid import uuid4, UUID
from datetime import datetime

from app.models.audit_log import AuditAction, AuditLog, TargetEntity
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.audit_log import GetAuditLogsRes, PaginatedResponse, AuditLogScheme

import logging

logger = logging.getLogger(__name__)

PAGE = 1
SIZE = 30

async def create_audit_log_item(
    db: AsyncSession,
    user_id: UUID | None = None, 
    action: AuditAction | None = None, 
    target_entity_type: TargetEntity | None = None,
    target_entity_id: UUID | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> AuditLog:
    """Creates an audit log entry and adds it to the current transaction."""


    logger.info(
        "create_audit_log_item: creating audit log action=%s entity=%s entity_id=%s user_id=%s",
        action,
        target_entity_type,
        target_entity_id,
        user_id,
    )
    _validate_required_create_fields(
        db=db,
        user_id=user_id,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        action=action
    )

    old_values, new_values = _validate_action_values(
        action,
        old_values,
        new_values
    )
    #TODO: check that id in table actually exists 
    #TODO: check the cases around the action and what is being done

    new_audit_log_item = AuditLog(
        id=uuid4(),
        user_id=user_id,
        action=action,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        new_values=new_values,
        old_values=old_values
    )

    db.add(new_audit_log_item)
    await db.commit()

    logger.info(
        "create_audit_log_item: successfully created audit log id=%s",
        new_audit_log_item.id,
    )

    return new_audit_log_item

def _validate_required_create_fields(db, user_id, target_entity_type, target_entity_id, action):
    """Validate required fields before creating an audit-log record."""
    logger.debug("_validate_required_create_fields: validating required fields")

    required = {
        "database_session": db,
        "user id": user_id,
        "target entity type": target_entity_type,
        "target entity id": target_entity_id,
        "action": action,
    }

    for name, value in required.items():
        if not value:
            logger.warning(
                "_validate_required_create_fields: missing %s",
                name,
            )
            raise HTTPException(400, f"Could not create audit log item. No {name} provided.")
        
def _validate_action_values(action, old_values, new_values):
    """Validate old and new value snapshots for the specified audit action."""
    logger.debug("_validate_action_values: validating action=%s", action)
    if action == AuditAction.DELETE:
        if not old_values: # old must exist
            logger.warning("_validate_action_values: DELETE missing old values")
            raise HTTPException(400, "Could not create audit log item. No old value provided.")
        return old_values, None
    
    elif action == AuditAction.UPDATE:
        if not old_values or not new_values:
            logger.warning("_validate_action_values: UPDATE missing old/new values")
            raise HTTPException(400, "Could not create audit log item. Either old or new values were not provided.")
        if old_values == new_values:
            logger.warning("_validate_action_values: UPDATE old and new values are identical")
            raise HTTPException(400, "Could not create audit log item. Old values and new values are the same.")
        return old_values, new_values

    elif action == AuditAction.CREATE:
        if not new_values:
            logger.warning("_validate_action_values: CREATE missing new values")
            raise HTTPException(400, "Could not create audit log item. New values were not provided.")
        return None, new_values
    
    return old_values, new_values


async def get_audit_logs_handler(
    page: int,
    size: int,
    db: AsyncSession,
    search_term: str | None = None,
    action: AuditAction | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort_order: str | None = None,
) -> GetAuditLogsRes:
    """Return filtered and paginated audit-log records."""
    logger.info(
        "get_audit_logs: page=%s size=%s search=%s action=%s",
        page,
        size,
        search_term,
        action,
    )

    #TODO: consider returning the username as well
    if not db:
        logger.error("get_audit_logs: database session missing")
        raise HTTPException(500, "No database.")

    _validate_pagination(page, size)

    stmt = select(AuditLog)

    logger.debug("get_audit_logs: applying filters")

    stmt = _apply_filters(stmt, search_term, action, start_date, end_date)
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar_one()

    logger.debug(
        "get_audit_logs: %s matching audit logs found",
        total_count,
    )

    offset = (page - 1) * size
    if total_count and offset >= total_count:
        logger.warning(
            "get_audit_logs: requested page=%s exceeds total pages",
            page,
        )
        raise HTTPException(422, "Request is beyond the total number of audit logs.")

    stmt = _apply_sort(stmt, sort_order).offset(offset).limit(size)
    result = await db.execute(stmt)
    
    audit_logs = result.scalars().all()

    logger.info(
        "get_audit_logs: retrieved %s audit logs",
        len(audit_logs),
    )

    results = [AuditLogScheme.model_validate(a) for a in audit_logs]

    logger.info("get_audit_logs: returning response")
    
    return GetAuditLogsRes(
        status=200,
        message="OK",
        data=PaginatedResponse[AuditLogScheme](
            total=total_count,
            page=page,
            size=size,
            results=results,
        ),
    )

def _validate_pagination(page, size):
    """Validate that audit-log pagination values are within allowed limits."""

    logger.debug(
        "_validate_pagination: page=%s size=%s",
        page,
        size,
    )

    if page < 1:
        logger.warning("_validate_pagination: invalid page=%s", page)
        raise HTTPException(422, "page must be >= 1")
    if size < 1:
        logger.warning("_validate_pagination: invalid size=%s", size)
        raise HTTPException(422, "size must be >= 1")
    
def _apply_filters(stmt, search_term, action, start_date, end_date):
    """Apply requested search, action, and date filters to an audit-log query."""

    logger.debug(
        "_apply_filters: search=%s action=%s",
        search_term,
        action,
    )

    if search_term:
        search_cols = [AuditLog.id, AuditLog.action, AuditLog.target_entity_type, AuditLog.target_entity_id]
        conditions = [cast(col, String).ilike(f"%{search_term}%") for col in search_cols]
        stmt = stmt.where(or_(*conditions))

    if action:
        stmt = stmt.where(AuditLog.action == action)

    if start_date:
        stmt = stmt.where(AuditLog.timestamp >= start_date)

    if end_date:
        stmt = stmt.where(AuditLog.timestamp <= end_date)
    
    return stmt

def _apply_sort(stmt, sort_order):
    """Apply chronological sorting to an audit-log query."""
    
    logger.debug(
        "_apply_sort: sort_order=%s",
        sort_order or "DESC",
    )

    sort_map = {
        "ASC": AuditLog.timestamp.asc(),
        "DESC": AuditLog.timestamp.desc(),
    }

    selected_order = sort_map.get(
        (sort_order or "DESC").upper(),
        AuditLog.timestamp.desc(),
    )

    return stmt.order_by(selected_order)