from celery import Celery

from app.config import settings

celery_app = Celery(
    "bot_builder",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks.ingest"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

import app.workers.tasks.ingest  # noqa: E402, F401
