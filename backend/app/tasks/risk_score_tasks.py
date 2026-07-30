import logging
from uuid import UUID

from sqlalchemy import select

from app.core.celery_app import celery
from app.core.database import SessionLocal
from app.models.neighbourhood import Neighbourhood
from app.services.risk_score_service import calculate_risk_score_handler


logger = logging.getLogger(__name__)


@celery.task
def recalculate_all_risk_scores():
    db = SessionLocal()
    try:
        neighbourhood_ids = db.execute(select(Neighbourhood.id)).scalars().all()
        for neighbourhood_id in neighbourhood_ids:
            calculate_risk_score_task.delay(str(neighbourhood_id))
    finally:
        db.close()

@celery.task
def calculate_risk_score_task(neighbourhood_id: str):
    db = SessionLocal()
    try:
        calculate_risk_score_handler(UUID(neighbourhood_id), db)

    except Exception:
        db.rollback()
        logger.exception("Failed to calculate risk score for neighbourhood %s", neighbourhood_id)

    finally:
        db.close()