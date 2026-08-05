from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.core.database import DbSession
from app.models.risk_threshold_config import RiskThresholdConfig
from app.schemas.risk_threshold_config import RiskThresholdConfigRes, UpdateRiskThresholdConfigReq


async def get_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, "Not authorised for this neighbourhood")
    
    stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id == neighbourhood_id)
    result = await db.execute(stmt)
    neighbourhood_risk_config = result.scalar_one_or_none()

    if not neighbourhood_risk_config:
        stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id.is_(None))
        result = await db.execute(stmt)
        neighbourhood_risk_config = result.scalar_one() #need to put a default in seed script

    return RiskThresholdConfigRes(
        id=neighbourhood_risk_config.id,
        neighbourhood_id=neighbourhood_risk_config.neighbourhood_id,
        low_max=neighbourhood_risk_config.low_max,
        medium_max=neighbourhood_risk_config.medium_max,
        updated_at=neighbourhood_risk_config.updated_at
    )


async def update_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, req: UpdateRiskThresholdConfigReq,db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, "Not authorised for this neighbourhood")
    

    update_data = req.model_dump(exclude_unset=True)
    
    stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id == neighbourhood_id)
    result = await db.execute(stmt)
    neighbourhood_risk_config = result.scalar_one_or_none()

    if not neighbourhood_risk_config:

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
        raise HTTPException(status_code=422, detail="low_max must be medium_max")
    
    await db.commit()
    await db.refresh(neighbourhood_risk_config)

    return RiskThresholdConfigRes.model_validate(neighbourhood_risk_config)
    

