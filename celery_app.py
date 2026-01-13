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

# Clean up old slots when Celery worker starts
from celery.signals import worker_ready

@worker_ready.connect
def on_worker_ready(sender=None, **kwargs):
    """Clean up old availability slots when Celery worker starts"""
    try:
        from app import app, cleanup_old_slots
        with app.app_context():
            deleted_count = cleanup_old_slots()
            print(f"[Worker Startup] ✓ Cleaned up {deleted_count} old availability slots")
    except Exception as e:
        import warnings
        warnings.warn(f"Could not clean up old slots on worker startup: {e}")

# Trigger task immediately when Beat starts (only once on startup)
from celery.signals import beat_init

@beat_init.connect
def on_beat_init(sender=None, **kwargs):
    """Trigger initial refresh cycle immediately when Beat starts.
    The cycle will automatically trigger the next cycle when it completes.
    Can filter venues using CELERY_VENUES_FILTER environment variable (comma-separated list).
    
    To hardcode specific venues, uncomment and modify the venues_filter line below.
    """
    try:
        from app import refresh_all_venues_task
        import os
        
        # OPTION 1: Use environment variable (recommended for flexibility)
        venues_filter = None
        env_filter = os.getenv('CELERY_VENUES_FILTER')
        if env_filter:
            venues_filter = [v.strip() for v in env_filter.split(',')]
            print(f"[Beat Startup] Venue filter from environment: {venues_filter}")
        
        # OPTION 2: Hardcode specific venues (uncomment to use)
        # venues_filter = ['puttery_nyc', 'kick_axe_brooklyn']
        # print(f"[Beat Startup] Using hardcoded venue filter: {venues_filter}")
        
        result = refresh_all_venues_task.delay(venues_filter=venues_filter)
        print(f"[Beat Startup] ✓ Triggered initial refresh cycle immediately (ID: {result.id})")
        if venues_filter:
            print(f"[Beat Startup] Filtered to venues: {venues_filter}")
            print(f"[Beat Startup] Expected tasks: {len(venues_filter)} venues × 7 guests × 30 days = {len(venues_filter) * 7 * 30} tasks per cycle")
        print(f"[Beat Startup] Cycle will run now, then automatically trigger next cycle when complete")
        print(f"[Beat Startup] Cycles will continue automatically until worker stops")
    except Exception as e:
        import warnings
        warnings.warn(f"Could not trigger initial refresh on Beat startup: {e}")

