from app.core.database import DbSession
from app.auth.dependencies import get_current_user, require_role
from app.schemas.pairing_token import LinkPropertyTokenRes
from app.schemas.pairing_token import EdgeAgentsCredentialsRes
from app.services.pairing_token import get_pairing_token_handler, pair_agent_handler
from app.auth.rate_limiter import limiter

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Request


router = APIRouter(prefix="/pairing-token", tags=["pairing-token"])

@router.get("/{property_id}") #Private
@limiter.limit("20/minute")
async def get_pairing_token(
    request: Request,
    property_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(require_role('RESIDENT', 'NEIGHBOURHOOD_ADMIN'))],
) -> LinkPropertyTokenRes:
    """Creates a pairing token and returns it to the user for the user to link their always on device."""

    return await get_pairing_token_handler(property_id, db, claims)

@router.get("/token/{pairing_token}")
@limiter.limit("10/minute")  # Limit to 10 requests per minute
async def pair_agent(
    request: Request,
    pairing_token: str,
    db: DbSession,
) -> EdgeAgentsCredentialsRes:
    """Creates an entry in the edge agents credentials table and returns the api key """

    return await pair_agent_handler(
        pairing_token,
        db
    )