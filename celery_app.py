from celery import Celery
import os

# Get Redis URL from environment or use default
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'availability_scraper',
    broker=redis_url,
    backend=redis_url,
    include=['app']  # This tells Celery to import the 'app' module to discover tasks
)

# Import app module to ensure tasks are registered
# This is important for Beat to discover scheduled tasks
try:
    import app
except ImportError as e:
    # If app can't be imported, log warning but continue
    # This might happen if Flask context is needed, but tasks should still register
    import warnings
    warnings.warn(f"Could not import app module: {e}. Tasks may not be discoverable.")

# Celery configuration
import sys

# Use threads pool on Windows for parallel processing (prefork doesn't work well on Windows)
# threads pool allows multiple tasks to run in parallel within a single worker
if sys.platform == 'win32':
    worker_pool = 'threads'
    worker_concurrency = 5  # Number of parallel threads (adjust based on your PC's performance)
else:
    worker_pool = 'prefork'
    worker_concurrency = 4

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
    worker_concurrency=worker_concurrency,
    worker_max_tasks_per_child=10 if worker_pool != 'solo' else None,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'refresh-all-venues': {
        'task': 'app.refresh_all_venues_task',
        'schedule': 1800.0,  # Every 30 minutes - refresh 30 days of slots (split into smaller chunks)
    },
}

