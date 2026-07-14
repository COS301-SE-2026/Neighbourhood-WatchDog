from app.core.database import DbSession
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from app.models.risk_score_history import RiskScoreHistory
from app.schemas.risk_score_history import RiskScoreRes

def get_neighbourhood_score_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskScoreRes:


    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, "Not authorised for this neighbourhood")
    
    stmt = (
        select(RiskScoreHistory)
        .where(RiskScoreHistory.neighbourhood_id == neighbourhood_id)
        .order_by(RiskScoreHistory.calculated_at.desc())
        .limit(1))
    
    latest_score = db.execute(stmt).scalar_one_or_none()

    if not latest_score:
        raise HTTPException(status_code=404, detail="No risk score calculated yet for this neighbourhood")
    
    return RiskScoreRes(
        neighbourhood_id=latest_score.neighbourhood_id,
        score=latest_score.score,
        classification=latest_score.classification,
        alert_count=latest_score.alert_count,
        calculated_at=latest_score.calculated_at
    )



def get_neighbourhood_score_history_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> list[RiskScoreRes]:
    pass