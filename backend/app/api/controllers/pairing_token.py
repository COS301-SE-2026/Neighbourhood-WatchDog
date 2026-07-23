from app.auth.rbac import require_role
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.schemas.pairing_token import LinkPropertyTokenRes
from app.services.pairing_token import get_pairing_token_handler

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/pairing-token", tags=["pairing-token"])

@router.get("/{property_id}")
async def get_pairing_token(
    property_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
) -> LinkPropertyTokenRes:
    """Creates a pairing token and returns it to the user for the user to link their always on device."""
    require_role(claims, ['RESIDENT'])
    return get_pairing_token_handler(property_id, db)