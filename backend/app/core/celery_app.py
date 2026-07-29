from datetime import timedelta
import os

from celery import Celery


celery = Celery(
    __name__,
    include=["app.tasks.risk_score_tasks"]
)

celery.conf.broker_url = os.environ.get("REDIS_URL")
celery.conf.result_backend = os.environ.get("REDIS_URL")

celery.conf.beat_schedule = {
    "recalculate-risk-scores-every-5-minutes": {
        "task": "app.tasks.risk_score_tasks.recalculate_all_risk_scores",
        "schedule": timedelta(minutes=5),
    }
}