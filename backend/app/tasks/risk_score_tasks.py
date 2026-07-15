import logging

from app.core.celery_app import celery
from app.core.database import SessionLocal
from app.services.risk_score_service import calculate_risk_score_handler


logger = logging.getLogger(__name__)


@celery.task
def recalculate_all_risk_scores():
    pass

@celery.task
def calculate_risk_score_task(neighbourhood_id: str):
    db = SessionLocal()
    try:
        calculate_risk_score_handler(neighbourhood_id, db)

    except Exception:
        db.rollback()
        logger.exception("Failed to calculate risk score for neighbourhood %s", neighbourhood_id)

    finally:
        db.close()
