from datetime import datetime

from app.core.database import DbSession
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, func
from app.auth.dependencies import get_user_by_claims
from app.models.risk_score_history import RiskScoreHistory
from app.schemas.risk_score_history import RiskScoreRes
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property
from app.models.property_user import PropertyUser
import logging

logger = logging.getLogger(__name__)

VALID_GRANULARITIES = {"minute", "hour", "day", "week"}

async def get_neighbourhood_score_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskScoreRes:
    """Returns most recently calculated risk score for a neighbourhood"""

    user = await get_user_by_claims(claims, db)

    if user is None:
        logger.warning("get_neigbourhood_risk_threshold: unauthorised access attempt for neighbourhood_id=%s", neighbourhood_id)
        raise HTTPException(401, "Could not get neighbourhood risk threshold. User not authenticated.")

    stmt = (
        select(Neighbourhood)
        .join(Property, Property.neighbourhood_id == Neighbourhood.id)
        .join(PropertyUser, PropertyUser.property_id == Property.id)
        .where(
            Neighbourhood.id == neighbourhood_id,
            PropertyUser.user_id == user.id,
        )
    )
    result = await db.execute(stmt)
    caller_neighbourhood = result.scalars().first()

    if not caller_neighbourhood:
        logger.warning("get_neighbourhood_score: unauthorised access attempt for neighbourhood_id=%s", neighbourhood_id)
        raise HTTPException(403, "Not authorised for this neighbourhood")
    
    stmt = (
        select(RiskScoreHistory)
        .where(RiskScoreHistory.neighbourhood_id == neighbourhood_id)
        .order_by(RiskScoreHistory.calculated_at.desc())
        .limit(1)
        )

    result = await db.execute(stmt)
    latest_score = result.scalar_one_or_none()

    if not latest_score:
        logger.warning("get_neigbourhood_score: no risk score calculated yet for neighbourhood_id=%s", neighbourhood_id)
        raise HTTPException(status_code=404, detail="No risk score calculated yet for this neighbourhood")

    logger.info("get_neigbourhood_score: latest score retrieved for neighbourhood_id=%s score=%s classification=%s", neighbourhood_id, latest_score.score, latest_score.classification)
    return RiskScoreRes(
        neighbourhood_id=latest_score.neighbourhood_id,
        score=latest_score.score,
        classification=latest_score.classification,
        alert_count=latest_score.alert_count,
        calculated_at=latest_score.calculated_at
    )



async def get_neighbourhood_score_history_handler(
    neighbourhood_id: UUID,
    granularity: str,
    db: DbSession,
    claims: dict,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[RiskScoreRes]:
    """Returns bucketed (by granularity) historical risk scores for a neighbourhood over a date range"""

    user = await get_user_by_claims(claims, db)

    if user is None:
        logger.warning("get_neigbourhood_risk_threshold: unauthorised access attempt for neighbourhood_id=%s", neighbourhood_id)
        raise HTTPException(401, "Could not get neighbourhood risk threshold. User not authenticated.")
    
    stmt = (
        select(Neighbourhood)
        .join(Property, Property.neighbourhood_id == Neighbourhood.id)
        .join(PropertyUser, PropertyUser.property_id == Property.id)
        .where(
            Neighbourhood.id == neighbourhood_id,
            PropertyUser.user_id == user.id,
        )
    )
    result = await db.execute(stmt)
    caller_neighbourhood = result.scalars().first()

    if not caller_neighbourhood:
        logger.warning("get_neigbourhood_score_history: unauthorised access attempt for neighbourhood_id=%s", neighbourhood_id)
        raise HTTPException(403, "Not authorised for this neighbourhood")

    if granularity not in VALID_GRANULARITIES:
        logger.warning("get_neigbourhood_score_history: invalid granularity=%s requested for neighbourhood_id=%s", granularity, neighbourhood_id)
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

    result = await db.execute(stmt)
    neighbourhood_history = result.all()

    if not neighbourhood_history:
        logger.warning("get_neigbourhood_score_history: no history found for neighbourhood_id=%s granularity=%s start=%s end=%s", neighbourhood_id, granularity, start, end)
        return []
    
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

    logger.info("get_neigbourhood_score_history:retrieved %d bucked results for neighbourhood_id=%s granularity=%s", len(neighbourhood_history_scores), neighbourhood_id, granularity)
    return neighbourhood_history_scores