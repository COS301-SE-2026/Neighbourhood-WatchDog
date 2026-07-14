from uuid import UUID

from app.core.database import DbSession
from app.schemas.risk_threshold_config import RiskThresholdConfigRes


def get_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    pass

def update_neighbourhood_risk_threshold_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskThresholdConfigRes:
    pass