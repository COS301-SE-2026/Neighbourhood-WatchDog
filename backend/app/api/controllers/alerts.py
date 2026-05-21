from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.alert import AlertCreate, AlertResponse
from app.services import alert_service

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)


@router.post("/", response_model=AlertResponse)
async def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    return await alert_service.create_alert(db, alert)