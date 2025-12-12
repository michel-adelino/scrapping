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
try:
    import app
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import app module: {e}. Tasks may not be discoverable.")

# Celery configuration
import sys

# Use threads pool on Windows for parallel processing
if sys.platform == 'win32':
    worker_pool = 'threads'
    worker_concurrency = 5
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
# DISABLED: Automatic refresh is disabled - task will only run when manually triggered
# celery_app.conf.beat_schedule = {
#     'refresh-all-venues': {
#         'task': 'app.refresh_all_venues_task',
#         'schedule': 1800.0,  # Every 30 minutes (1800 seconds)
#     },
# }

# Trigger task immediately when Beat starts (only once on startup)
from celery.signals import beat_init

@beat_init.connect
def on_beat_init(sender=None, **kwargs):
    """Trigger initial refresh cycle immediately when Beat starts.
    The cycle will automatically trigger the next cycle when it completes."""
    try:
        from app import refresh_all_venues_task
        result = refresh_all_venues_task.delay()
        print(f"[Beat Startup] ✓ Triggered initial refresh cycle immediately (ID: {result.id})")
        print(f"[Beat Startup] Cycle will run now, then automatically trigger next cycle when complete")
        print(f"[Beat Startup] Cycles will continue automatically until worker stops")
    except Exception as e:
        import warnings
        warnings.warn(f"Could not trigger initial refresh on Beat startup: {e}")

