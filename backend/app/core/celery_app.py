import os
from datetime import timedelta
from celery import Celery
from celery.signals import worker_process_init

from app.core.database import worker_engine

@worker_process_init.connect
def reset_engine_after_fork(**kwargs):
    worker_engine.sync_engine.dispose(close=False)

celery = Celery(
    __name__,
    include=["app.tasks.risk_score_tasks", "app.tasks.clip_tasks"]
)

celery.conf.broker_url = os.environ.get("REDIS_URL")
celery.conf.result_backend = os.environ.get("REDIS_URL")

celery.conf.beat_schedule = {
    "recalculate-risk-scores-every-5-minutes": {
        "task": "app.tasks.risk_score_tasks.recalculate_all_risk_scores",
        "schedule": timedelta(minutes=5),
    }
}