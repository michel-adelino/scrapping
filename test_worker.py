#!/usr/bin/env python3
"""
Test script to manually trigger a task and verify worker is processing
Run this to send a task to the worker and see if it gets processed
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Celery Worker - Manual Task Trigger")
print("=" * 60)

try:
    from celery_app import celery_app
    from app import refresh_all_venues_task
    
    print("\n1. Sending task to worker...")
    result = refresh_all_venues_task.delay()
    
    print(f"   ✓ Task sent successfully!")
    print(f"   Task ID: {result.id}")
    print(f"   Task State: {result.state}")
    
    print("\n2. Check your worker terminal - you should see:")
    print("   [timestamp] Task app.refresh_all_venues_task[task-id] received")
    print("   [timestamp] Task app.refresh_all_venues_task[task-id] started")
    
    print("\n3. Waiting 5 seconds to check task state...")
    import time
    time.sleep(5)
    
    result.refresh()  # Refresh task state
    print(f"   Task State (after 5s): {result.state}")
    
    if result.state == 'SUCCESS':
        print(f"   ✓ Task completed successfully!")
        print(f"   Result: {result.result}")
    elif result.state == 'PENDING':
        print(f"   ⚠ Task is still pending - worker might not be running")
        print(f"   Make sure worker is running: python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info")
    elif result.state == 'STARTED':
        print(f"   ✓ Task is being processed by worker!")
    elif result.state == 'FAILURE':
        print(f"   ✗ Task failed: {result.info}")
    else:
        print(f"   Task state: {result.state}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

