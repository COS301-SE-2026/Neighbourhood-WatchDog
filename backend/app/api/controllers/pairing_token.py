from app.core.database import DbSession
from app.auth.dependencies import require_role
from app.schemas.pairing_token import LinkPropertyTokenRes
from app.schemas.pairing_token import EdgeAgentsCredentialsRes
from app.services.pairing_token import get_pairing_token_handler, pair_agent_handler
from app.auth.rate_limiter import limiter

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from app.auth.authorization import Claims, PropertyAdminClaims

router = APIRouter(prefix="/pairing-token", tags=["pairing-token"])

@router.get(
    "/{property_id}",
    response_model=LinkPropertyTokenRes,
    status_code=200,
    responses={
        400: {"description": "No property ID provided."},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions to generate a pairing token"},
        404: {"description": "User not found"},
        500: {"description": "No database"},
    },
) #Private
@limiter.limit("20/minute")
async def get_pairing_token(
    request: Request,
    property_id: UUID,
    db: DbSession,
    claims: PropertyAdminClaims,
) -> LinkPropertyTokenRes:
    """Creates a pairing token and returns it to the user for the user to link their always on device."""
    return await get_pairing_token_handler(property_id, db, claims)

@router.get(
    "/token/{pairing_token}",
    response_model=EdgeAgentsCredentialsRes,
    status_code=201,
    responses={
        400: {"description": "Token is expired or invalid"},
        404: {"description": "Property does not exist"},
        500: {"description": "No database"},
    },
)
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