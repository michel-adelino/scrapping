#!/usr/bin/env python3
"""
Test script to verify the Swingers NYC scraper function
This script tests the scrape_swingers_task function directly
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Swingers NYC Scraper")
print("=" * 60)

# Import required modules
try:
    from app import app, db, AvailabilitySlot, ScrapingTask
    from app import scrape_swingers_task
    print("✓ Successfully imported app and scrape_swingers_task")
except Exception as e:
    print(f"✗ Failed to import modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test parameters
guests = 6
# Use a date in the future (e.g., 30 days from now)
target_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

print(f"\nTest Parameters:")
print(f"  - Guests: {guests}")
print(f"  - Target Date: {target_date}")
print(f"  - URL will be: https://www.swingers.club/us/locations/nyc/book-now?guests={guests}&search[month]={datetime.strptime(target_date, '%Y-%m-%d').month}&search[year]={datetime.strptime(target_date, '%Y-%m-%d').year}&depart={target_date}")

# Option 1: Test the function directly (without Celery)
print("\n" + "=" * 60)
print("Option 1: Testing function directly (synchronous)")
print("=" * 60)

try:
    with app.app_context():
        # Create a mock task object (since it's a Celery task)
        class MockTask:
            pass
        
        mock_task = MockTask()
        
        print(f"\nStarting scraper...")
        print(f"This will open a browser and scrape slots for {target_date}")
        print(f"Press Ctrl+C to cancel if needed\n")
        
        # Call the function directly
        result = scrape_swingers_task(mock_task, guests, target_date, task_id=None)
        
        print(f"\n✓ Scraper completed successfully!")
        print(f"  Result: {result}")
        
        # Check database for saved slots
        slots = AvailabilitySlot.query.filter(
            AvailabilitySlot.venue_name == 'Swingers (NYC)',
            AvailabilitySlot.date == datetime.strptime(target_date, "%Y-%m-%d").date(),
            AvailabilitySlot.guests == guests
        ).all()
        
        print(f"\n✓ Found {len(slots)} slots in database for Swingers (NYC) on {target_date}")
        
        if slots:
            print(f"\nSample slots:")
            for i, slot in enumerate(slots[:5], 1):  # Show first 5
                print(f"  {i}. Time: {slot.time}, Price: {slot.price}, Status: {slot.status}")
            if len(slots) > 5:
                print(f"  ... and {len(slots) - 5} more slots")
        else:
            print(f"\n⚠ No slots found in database. This could mean:")
            print(f"  - No slots available for that date")
            print(f"  - The scraper didn't find any slots")
            print(f"  - There was an issue with slot extraction")
            
except KeyboardInterrupt:
    print("\n\n⚠ Test cancelled by user")
except Exception as e:
    print(f"\n✗ Error during scraping: {e}")
    import traceback
    traceback.print_exc()

# Option 2: Test via API endpoint
print("\n" + "=" * 60)
print("Option 2: Testing via API endpoint")
print("=" * 60)

print(f"\nTo test via API, you can use curl or Postman:")
print(f"\ncurl -X POST http://localhost:5000/run_scraper \\")
print(f"  -H 'Content-Type: application/json' \\")
print(f"  -d '{{")
print(f'    "website": "swingers_nyc",')
print(f'    "guests": {guests},')
print(f'    "target_date": "{target_date}"')
print(f"  }}'")

print(f"\nOr using Python requests:")
print(f"""
import requests

response = requests.post('http://localhost:5000/run_scraper', json={{
    'website': 'swingers_nyc',
    'guests': {guests},
    'target_date': '{target_date}'
}})

print(response.json())
task_id = response.json()['task_id']

# Then check task status:
status_response = requests.get(f'http://localhost:5000/api/task_status/{{task_id}}')
print(status_response.json())
""")

# Option 3: Check existing data
print("\n" + "=" * 60)
print("Option 3: Check existing Swingers NYC data in database")
print("=" * 60)

try:
    with app.app_context():
        # Count all Swingers NYC slots
        total_slots = AvailabilitySlot.query.filter(
            AvailabilitySlot.venue_name == 'Swingers (NYC)'
        ).count()
        
        print(f"\n✓ Total Swingers (NYC) slots in database: {total_slots}")
        
        if total_slots > 0:
            # Get recent slots
            recent_slots = AvailabilitySlot.query.filter(
                AvailabilitySlot.venue_name == 'Swingers (NYC)'
            ).order_by(AvailabilitySlot.date.desc()).limit(10).all()
            
            print(f"\nRecent slots:")
            for slot in recent_slots:
                print(f"  - Date: {slot.date}, Time: {slot.time}, Price: {slot.price}, Guests: {slot.guests}")
            
            # Get unique dates
            unique_dates = db.session.query(AvailabilitySlot.date).filter(
                AvailabilitySlot.venue_name == 'Swingers (NYC)'
            ).distinct().order_by(AvailabilitySlot.date.desc()).limit(10).all()
            
            print(f"\nDates with available slots:")
            for date_tuple in unique_dates:
                date_str = str(date_tuple[0])
                count = AvailabilitySlot.query.filter(
                    AvailabilitySlot.venue_name == 'Swingers (NYC)',
                    AvailabilitySlot.date == date_tuple[0]
                ).count()
                print(f"  - {date_str}: {count} slots")
        else:
            print(f"\n⚠ No Swingers (NYC) slots found in database")
            
except Exception as e:
    print(f"\n✗ Error checking database: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\nTips:")
print("  1. Make sure the Flask app is running if testing via API")
print("  2. Make sure Celery worker is running if using async tasks")
print("  3. Check browser console/logs for any JavaScript errors")
print("  4. Verify the URL format matches the expected format")
print("  5. Check that slots are being found with the correct selectors")

