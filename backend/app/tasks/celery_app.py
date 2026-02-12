"""Celery application factory and configuration."""

from __future__ import annotations

import os

from celery import Celery
from kombu import Queue

# Handle import for when Celery runs standalone (outside FastAPI)
try:
    from app.core.config import settings

    _broker_url = settings.UPSTASH_REDIS_URL
except Exception:
    _broker_url = os.environ.get("UPSTASH_REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("trendedge")

celery_app.conf.update(
    broker_url=_broker_url,
    result_backend=_broker_url,
    # Serialization — never use pickle
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Time
    timezone="UTC",
    enable_utc=True,
    # Task tracking
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Result expiry
    result_expires=3600,
    # Worker limits
    worker_max_tasks_per_child=200,
    worker_max_memory_per_child=512000,  # KB
    # Broker transport
    broker_transport_options={"visibility_timeout": 600},
    # Queues
    task_queues=[
        Queue("high", routing_key="high"),
        Queue("default", routing_key="default"),
        Queue("low", routing_key="low"),
        Queue("notifications", routing_key="notifications"),
    ],
    task_default_queue="default",
    task_default_routing_key="default",
    # Task routes
    task_routes={
        "app.tasks.*.process_webhook": {"queue": "high"},
        "app.tasks.*.send_*": {"queue": "notifications"},
    },
)
