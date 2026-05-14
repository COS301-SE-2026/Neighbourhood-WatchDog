from fastapi import FastAPI, APIRouter, Depends, HTTPException
from backend.app.schemas.property import CreatePropertyReq, CreatePropertyRes
from app.core.database import DbSession
from services.property_service import create_property_handler

router = APIRouter(prefix="/properties", tags=["property"])

@router.post("create-property")
async def create_property(req: CreatePropertyReq, db: DbSession):
    """Create property endpoint returns the property object that was created"""
    create_property_handler(req, db)