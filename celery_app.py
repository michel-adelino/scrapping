from celery import Celery
import os

# Get Redis URL from environment or use default
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'availability_scraper',
    broker=redis_url,
    backend=redis_url,
    include=['app']
)

# Celery configuration
import sys

# Use solo pool on Windows (prefork doesn't work well on Windows)
worker_pool = 'solo' if sys.platform == 'win32' else 'prefork'

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes max per task
    task_soft_time_limit=1500,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_pool=worker_pool,
    worker_max_tasks_per_child=10 if worker_pool != 'solo' else None,  # Not applicable for solo pool
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'refresh-all-venues': {
        'task': 'app.refresh_all_venues_task',
        'schedule': 900.0,  # Every 15 minutes - refresh today and tomorrow slots
    },
}

