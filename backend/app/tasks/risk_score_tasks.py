from app.core.celery_app import celery
from app.core.database import SessionLocal

@celery.task
def recalculate_all_risk_scores():
    pass

@celery.task
def calculate_risk_score_task(neighbourhood_id: str):
    pass
