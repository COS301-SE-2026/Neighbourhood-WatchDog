from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.core.database import DbSession
from app.models.risk_threshold_config import RiskThresholdConfig
from app.schemas.risk_threshold_config import RiskThresholdConfigRes


def get_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, "Not authorised for this neighbourhood")
    
    stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id == neighbourhood_id)
    neighbourhood_risk_config = db.execute(stmt).scalar_one_or_none()

    if not neighbourhood_risk_config:
        stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id.is_(None))
        neighbourhood_risk_config = db.execute(stmt).scalar_one()

    return RiskThresholdConfigRes(
        id=neighbourhood_risk_config.id,
        neighbourhood_id=neighbourhood_risk_config.neighbourhood_id,
        low_max=neighbourhood_risk_config.low_max,
        medium_max=neighbourhood_risk_config.medium_max,
        updated_at=neighbourhood_risk_config.updated_at
    )


def update_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    pass