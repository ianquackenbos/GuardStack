"""
Celery Application Configuration

Configures Celery for GuardStack background task processing
with Redis as message broker and result backend.
"""

import os
from celery import Celery
from kombu import Queue

# Redis connection URL from environment or default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery application
celery_app = Celery(
    "guardstack",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
    include=[
        "guardstack.workers.tasks.reports",
        "guardstack.workers.tasks.evaluations",
        "guardstack.workers.tasks.discovery",
        "guardstack.workers.tasks.compliance",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 min soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    worker_max_tasks_per_child=100,
    
    # Result settings
    result_expires=86400,  # 24 hours
    result_extended=True,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("reports", routing_key="reports.*"),
        Queue("evaluations", routing_key="evaluations.*"),
        Queue("discovery", routing_key="discovery.*"),
        Queue("compliance", routing_key="compliance.*"),
    ),
    
    # Task routing
    task_routes={
        "guardstack.workers.tasks.reports.*": {"queue": "reports"},
        "guardstack.workers.tasks.evaluations.*": {"queue": "evaluations"},
        "guardstack.workers.tasks.discovery.*": {"queue": "discovery"},
        "guardstack.workers.tasks.compliance.*": {"queue": "compliance"},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Discovery scan every hour
        "discovery-scan-hourly": {
            "task": "guardstack.workers.tasks.discovery.scheduled_discovery_scan",
            "schedule": 3600.0,  # Every hour
            "options": {"queue": "discovery"},
        },
        # Compliance check every 6 hours
        "compliance-check-6h": {
            "task": "guardstack.workers.tasks.compliance.scheduled_compliance_check",
            "schedule": 21600.0,  # Every 6 hours
            "options": {"queue": "compliance"},
        },
        # Daily summary report
        "daily-summary-report": {
            "task": "guardstack.workers.tasks.reports.generate_daily_summary",
            "schedule": 86400.0,  # Every 24 hours
            "options": {"queue": "reports"},
        },
        # Posture score recalculation every 15 minutes
        "posture-recalculate-15m": {
            "task": "guardstack.workers.tasks.evaluations.recalculate_posture_scores",
            "schedule": 900.0,  # Every 15 minutes
            "options": {"queue": "evaluations"},
        },
    },
)


# Optional: Configure task monitoring with Flower
celery_app.conf.update(
    worker_send_task_events=True,
    task_send_sent_event=True,
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f"Request: {self.request!r}")
    return {"status": "ok", "worker": self.request.hostname}


if __name__ == "__main__":
    celery_app.start()
