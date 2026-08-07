from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.core.database import DbSession
from app.models.risk_threshold_config import RiskThresholdConfig
from app.schemas.risk_threshold_config import RiskThresholdConfigRes, UpdateRiskThresholdConfigReq
import logging

logger = logging.getLogger(__name__)

async def get_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    """Returns neighbourhood risk threshold config (falls back to default if none is set)"""

    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        logger.warning("get_neigbourhood_risk_threshold: unauthorised access attempt for neighbourhood_id=%s by caller_neighbourhood=%s", neighbourhood_id, caller_neighbourhood)
        raise HTTPException(403, "Not authorised for this neighbourhood")
    
    stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id == neighbourhood_id)
    result = await db.execute(stmt)
    neighbourhood_risk_config = result.scalar_one_or_none()

    if not neighbourhood_risk_config:
        logger.info("get_neigbourhood_risk_threshold: no config found for neighbourhood_id=%s, falling back to defualt", neighbourhood_id)
        stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id.is_(None))
        result = await db.execute(stmt)
        neighbourhood_risk_config = result.scalar_one() #need to put a default in seed script

    logger.info("get_neigbourhood_risk_threshold: config retrieved for neighbourhood_id=%s low_max=%s medium_max=%s", neighbourhood_id, neighbourhood_risk_config.low_max, neighbourhood_risk_config.medium_max)
    return RiskThresholdConfigRes(
        id=neighbourhood_risk_config.id,
        neighbourhood_id=neighbourhood_risk_config.neighbourhood_id,
        low_max=neighbourhood_risk_config.low_max,
        medium_max=neighbourhood_risk_config.medium_max,
        updated_at=neighbourhood_risk_config.updated_at
    )


async def update_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, req: UpdateRiskThresholdConfigReq,db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    """Updates a neighbourhood's risk threshold config, validating low_max < medium_max"""

    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        logger.warning("update_neigbourhood_risk_threshold: unauthorised access attempt for neigbourhood_id=%s by caller_neighbourhood=%s", neighbourhood_id, caller_neighbourhood)
        raise HTTPException(403, "Not authorised for this neighbourhood")
    

    update_data = req.model_dump(exclude_unset=True)
    
    stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id == neighbourhood_id)
    result = await db.execute(stmt)
    neighbourhood_risk_config = result.scalar_one_or_none()

    if not neighbourhood_risk_config:
        logger.info("get_neigbourhood_risk_threshold: no existing config for neigbourhood_id=%s, creating from default", neighbourhood_id)
        stmt_default = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id.is_(None))
        default_result = await db.execute(stmt_default)
        default_neighbourhood_risk_config = default_result.scalar_one()

        new_neighbourhood_risk_config = RiskThresholdConfig(
            neighbourhood_id=neighbourhood_id,
            low_max=default_neighbourhood_risk_config.low_max,
            medium_max=default_neighbourhood_risk_config.medium_max
        )

        db.add(new_neighbourhood_risk_config)

        neighbourhood_risk_config = new_neighbourhood_risk_config


    for field, value in update_data.items():
        setattr(neighbourhood_risk_config, field, value)

    if neighbourhood_risk_config.low_max >= neighbourhood_risk_config.medium_max:
        logger.warning("update_neighbourhood_risk_threshold: invalid thresholds for neighbourhood_id=%s low_max=%s medium_max=%s",neighbourhood_id, neighbourhood_risk_config.low_max, neighbourhood_risk_config.medium_max)
        raise HTTPException(status_code=422, detail="low_max must be medium_max")
    
    await db.commit()
    await db.refresh(neighbourhood_risk_config)

    logger.info("update_neighbourhood_risk_threshold: config updated for neighbourhood_id=%s low_max=%s medium_max=%s",neighbourhood_id, neighbourhood_risk_config.low_max, neighbourhood_risk_config.medium_max)
    return RiskThresholdConfigRes.model_validate(neighbourhood_risk_config)
    

