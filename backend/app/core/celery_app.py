import os
from datetime import timedelta
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

from app.core.database import worker_engine
from app.core.firebase import init_firebase

init_firebase()

@worker_process_init.connect
def reset_engine_after_fork(**kwargs):
    worker_engine.sync_engine.dispose(close=False)

celery = Celery(
    __name__,
    include=[
        "app.tasks.risk_score_tasks", 
        "app.tasks.clip_tasks", "app.tasks.push_tasks",
        "app.tasks.incident_density_tasks"
    ]
)

celery.conf.broker_url = os.environ.get("REDIS_URL")
celery.conf.result_backend = os.environ.get("REDIS_URL")
celery.conf.enable_utc = True
celery.conf.timezone = "Africa/Johannesburg"

celery.conf.beat_schedule = {
    "recalculate-risk-scores-every-5-minutes": {
        "task": "app.tasks.risk_score_tasks.recalculate_all_risk_scores",
        "schedule": timedelta(minutes=5),
    },
    "refresh-current-incident-density": {
        "task": (
            "app.tasks.incident_density_tasks."
            "refresh_current_incident_density"
        ),
        "schedule": timedelta(minutes=5),
    },
    "finalize-yesterday-incident-density": {
        "task": (
            "app.tasks.incident_density_tasks."
            "finalize_yesterday_incident_density"
        ),
        "schedule": crontab(
            hour=0,
            minute=15,
        ),
    }
}