from datetime import datetime

from app.core.database import DbSession
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.risk_score_history import RiskScoreHistory
from app.schemas.risk_score_history import RiskScoreRes

VALID_GRANULARITIES = {"minute", "hour", "day", "week"}

def get_neighbourhood_score_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskScoreRes:


    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, "Not authorised for this neighbourhood")
    
    stmt = (
        select(RiskScoreHistory)
        .where(RiskScoreHistory.neighbourhood_id == neighbourhood_id)
        .order_by(RiskScoreHistory.calculated_at.desc())
        .limit(1)
        )
    
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



def get_neighbourhood_score_history_handler(
    neighbourhood_id: UUID,
    granularity: str,
    db: DbSession,
    claims: dict,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[RiskScoreRes]:

    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, "Not authorised for this neighbourhood")
    
    if granularity not in VALID_GRANULARITIES:
        raise HTTPException(400, "Invalid granularity")
    
    bucket = func.date_trunc(granularity, RiskScoreHistory.calculated_at)
    
    ranked = (
        select(
            RiskScoreHistory.score,
            RiskScoreHistory.classification,
            RiskScoreHistory.alert_count,
            RiskScoreHistory.calculated_at,
            bucket.label("bucket"),
            func.row_number().over(
                partition_by=bucket,
                order_by=RiskScoreHistory.score.desc(),
            ).label("rn"),
        )
        .where(RiskScoreHistory.neighbourhood_id == neighbourhood_id)
    )

    if start:
        ranked = ranked.where(RiskScoreHistory.calculated_at >= start)
    if end:
        ranked = ranked.where(RiskScoreHistory.calculated_at <= end)

    ranked_subq = ranked.subquery()

    stmt = (
        select(ranked_subq)
        .where(ranked_subq.c.rn == 1)
        .order_by(ranked_subq.c.bucket.asc())
    )
        
    neighbourhood_history = db.execute(stmt).all()

    if not neighbourhood_history:
        raise HTTPException(status_code=404, detail="Neighbourhood does not have history")
    
    neighbourhood_history_scores = []
    for curr_neighbourhood_risk in neighbourhood_history:
        curr_risk = RiskScoreRes(
            neighbourhood_id=neighbourhood_id,
            score=curr_neighbourhood_risk.score,
            classification=curr_neighbourhood_risk.classification,
            alert_count=curr_neighbourhood_risk.alert_count,
            calculated_at=curr_neighbourhood_risk.calculated_at
        )

        neighbourhood_history_scores.append(curr_risk)

    return neighbourhood_history_scores