#!/usr/bin/env python3
"""
Test script to verify Celery setup
Run this to check if Celery can discover tasks and connect to Redis
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Celery Configuration")
print("=" * 60)

# Test 1: Redis connection
print("\n1. Testing Redis connection...")
try:
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url)
    result = r.ping()
    print(f"   ✓ Redis connection successful: {result}")
except Exception as e:
    print(f"   ✗ Redis connection failed: {e}")
    sys.exit(1)

# Test 2: Import celery_app
print("\n2. Testing Celery app import...")
try:
    from celery_app import celery_app
    print(f"   ✓ Celery app imported: {celery_app}")
    print(f"   ✓ Broker: {celery_app.conf.broker_url}")
    print(f"   ✓ Backend: {celery_app.conf.result_backend}")
except Exception as e:
    print(f"   ✗ Failed to import celery_app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import app module (to register tasks)
print("\n3. Testing app module import (task registration)...")
try:
    import app
    print(f"   ✓ App module imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import app module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check registered tasks
print("\n4. Checking registered tasks...")
try:
    registered_tasks = list(celery_app.tasks.keys())
    # Filter out built-in tasks
    user_tasks = [t for t in registered_tasks if not t.startswith('celery.')]
    print(f"   ✓ Found {len(user_tasks)} user-defined tasks:")
    for task in sorted(user_tasks)[:10]:  # Show first 10
        print(f"     - {task}")
    if len(user_tasks) > 10:
        print(f"     ... and {len(user_tasks) - 10} more")
    
    # Check for the beat schedule task
    if 'app.refresh_all_venues_task' in registered_tasks:
        print(f"   ✓ Beat schedule task 'app.refresh_all_venues_task' is registered")
    else:
        print(f"   ✗ WARNING: Beat schedule task 'app.refresh_all_venues_task' NOT found!")
        print(f"     Available tasks containing 'refresh':")
        refresh_tasks = [t for t in registered_tasks if 'refresh' in t.lower()]
        for task in refresh_tasks:
            print(f"       - {task}")
except Exception as e:
    print(f"   ✗ Error checking tasks: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check beat schedule
print("\n5. Checking Celery Beat schedule...")
try:
    beat_schedule = celery_app.conf.beat_schedule
    if beat_schedule:
        print(f"   ✓ Beat schedule configured with {len(beat_schedule)} entries:")
        for name, config in beat_schedule.items():
            print(f"     - {name}: {config.get('task', 'N/A')} (every {config.get('schedule', 'N/A')} seconds)")
    else:
        print(f"   ✗ WARNING: No beat schedule configured!")
except Exception as e:
    print(f"   ✗ Error checking beat schedule: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test task discovery
print("\n6. Testing task discovery...")
try:
    # Try to get the task
    task = celery_app.tasks.get('app.refresh_all_venues_task')
    if task:
        print(f"   ✓ Task 'app.refresh_all_venues_task' is discoverable")
    else:
        print(f"   ✗ Task 'app.refresh_all_venues_task' NOT found in tasks registry")
        print(f"     This means Beat won't be able to schedule it!")
except Exception as e:
    print(f"   ✗ Error testing task discovery: {e}")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)
print("\nIf tasks are not registered, make sure:")
print("  1. Flask app is imported (import app)")
print("  2. Tasks are decorated with @celery_app.task")
print("  3. celery_app is imported in app.py before tasks are defined")
print("\nTo fix Beat, try:")
print("  1. Make sure Flask app is running (or at least imported)")
print("  2. Restart Beat: python -m celery -A celery_app beat --loglevel=debug")
print("  3. Check Beat logs for task discovery messages")

