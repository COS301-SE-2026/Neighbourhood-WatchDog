from app.core.database import DbSession
from uuid import UUID

from app.schemas.risk_score_history import RiskScoreRes

def get_neighbourhood_score_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RiskScoreRes:
    pass