from fastapi import APIRouter, Depends, HTTPException
from app.schemas.property import CreatePropertyReq, CreatePropertyRes
from app.services.property_service import create_property_handler
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role

router = APIRouter(prefix="/properties", tags=["properties"])

@router.post("/create-property")
async def create_property(req: CreatePropertyReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Create property endpoint returns the property object that was created"""

    require_role(['Resident'])
    new_property = await create_property_handler(req.address, req.property_type, db, claims)

    return CreatePropertyRes(
        201,
        "Property Created Successful",
        new_property
    )
