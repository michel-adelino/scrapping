# Troubleshooting Celery Beat and Worker

## Symptoms

### Beat Process: Shows "Starting..." then nothing
- Beat starts but doesn't show schedule information
- No periodic tasks are being executed

### Worker Process: Shows "ready" but no tasks processing
- Worker is connected and ready
- But no tasks are being processed

## Quick Diagnostic

Run the diagnostic script:
```bash
source venv/bin/activate
python test_celery.py
```

This will check:
1. Redis connection
2. Celery app import
3. Task registration
4. Beat schedule configuration

## Common Issues and Fixes

### Issue 1: Tasks Not Discovered by Beat

**Symptom:** Beat shows "Starting..." then nothing, no schedule info

**Cause:** Beat needs to import the `app` module to discover tasks

**Fix:**
1. Make sure `celery_app.py` has `include=['app']` (already configured)
2. The `celery_app.py` now tries to import `app` module automatically
3. Restart Beat:
   ```bash
   source venv/bin/activate
   python -m celery -A celery_app beat --loglevel=debug
   ```

**Expected output when working:**
```
celery beat v5.x.x is starting.
__    -    _______
Configuration ->
    . broker -> redis://localhost:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat:PersistentScheduler
    . db -> celerybeat-schedule
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 minutes (300s)
<celery.beat.Scheduler: Scheduler>
Scheduler: Sending due task refresh-all-venues (app.refresh_all_venues_task)
```

### Issue 2: Worker Can't See Tasks

**Symptom:** Worker shows "ready" but tasks aren't processed

**Fix:**
1. Check if tasks are registered:
   ```bash
   source venv/bin/activate
   python -m celery -A celery_app inspect registered
   ```

2. You should see tasks like:
   - `app.refresh_all_venues_task`
   - `app.scrape_all_venues_task`
   - `app.scrape_venue_task`
   - etc.

3. If no tasks appear, make sure Flask app is running or at least imported:
   ```bash
   source venv/bin/activate
   python -c "import app; from celery_app import celery_app; print(list(celery_app.tasks.keys()))"
   ```

### Issue 3: Redis Connection Issues

**Symptom:** Worker shows connection errors or "all alone"

**Fix:**
1. Check Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. If Redis is not running:
   ```bash
   sudo systemctl start redis-server
   # Or manually:
   redis-server
   ```

3. Check Redis URL in celery_app.py matches your setup

### Issue 4: Beat Schedule Not Working

**Symptom:** Beat runs but scheduled tasks never execute

**Fix:**
1. Check the schedule is configured correctly in `celery_app.py`:
   ```python
   celery_app.conf.beat_schedule = {
       'refresh-all-venues': {
           'task': 'app.refresh_all_venues_task',  # Must match task name exactly
           'schedule': 1800.0,  # Every 30 minutes
       },
   }
   ```

2. Verify task name matches:
   - Schedule uses: `'app.refresh_all_venues_task'`
   - Task decorator: `@celery_app.task(name='app.refresh_all_venues_task')`
   - These must match exactly!

3. Check Beat logs with debug level:
   ```bash
   python -m celery -A celery_app beat --loglevel=debug
   ```

### Issue 5: Circular Import Issues

**Symptom:** Import errors when starting Beat or Worker

**Fix:**
1. The code is designed to handle circular imports
2. `app.py` imports `celery_app` after Flask app is created
3. `celery_app.py` imports `app` to register tasks
4. If you see import errors, check the import order

## Step-by-Step Debugging

### Step 1: Verify Redis
```bash
redis-cli ping
# Should return: PONG
```

### Step 2: Run Diagnostic
```bash
source venv/bin/activate
python test_celery.py
```

### Step 3: Check Task Registration
```bash
source venv/bin/activate
python -m celery -A celery_app inspect registered
```

### Step 4: Test Beat with Debug
```bash
source venv/bin/activate
python -m celery -A celery_app beat --loglevel=debug
```

Look for:
- "Scheduler: Sending due task" messages
- Task discovery messages
- Any error messages

### Step 5: Test Worker
```bash
source venv/bin/activate
python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info
```

Look for:
- "celery@hostname ready" message
- Task received/started messages when tasks are sent

### Step 6: Manually Trigger a Task
```bash
source venv/bin/activate
python -c "
from celery_app import celery_app
from app import refresh_all_venues_task
result = refresh_all_venues_task.delay()
print(f'Task ID: {result.id}')
print(f'Task state: {result.state}')
"
```

Then check worker logs to see if it processes the task.

## Expected Behavior

### When Everything Works:

**Beat:**
```
celery beat v5.x.x is starting.
...
Scheduler: Sending due task refresh-all-venues (app.refresh_all_venues_task)
```

**Worker:**
```
celery@hostname ready.
[timestamp] Task app.refresh_all_venues_task[task-id] received
[timestamp] Task app.refresh_all_venues_task[task-id] started
[timestamp] Task app.refresh_all_venues_task[task-id] succeeded
```

## Still Not Working?

1. Check all processes are using the same virtual environment
2. Verify all processes are in the same directory
3. Check for any error messages in logs
4. Try restarting all processes:
   - Stop Beat (Ctrl+C)
   - Stop Worker (Ctrl+C)
   - Restart Worker first
   - Then restart Beat
5. Check if Flask app needs to be running for tasks to work (some tasks use `app.app_context()`)

