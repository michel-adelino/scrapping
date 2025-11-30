#!/usr/bin/env python3
"""
Quick test script for Swingers NYC scraper
Tests URL construction and provides simple testing instructions
"""

import sys
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Quick Test: Swingers NYC URL Construction")
print("=" * 60)

# Test parameters
guests = 6
target_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

# Parse the target date
dt = datetime.strptime(target_date, "%Y-%m-%d")
month = dt.month
year = dt.year
day = dt.strftime("%d")
month_abbr = dt.strftime("%b")

# Construct the URL (same as in the function)
query_params = {
    'guests': str(guests),
    'search[month]': str(month),
    'search[year]': str(year),
    'depart': target_date
}
url = f"https://www.swingers.club/us/locations/nyc/book-now?{urlencode(query_params)}"

print(f"\nTest Parameters:")
print(f"  Guests: {guests}")
print(f"  Target Date: {target_date}")
print(f"  Day: {day}")
print(f"  Month (abbr): {month_abbr}")
print(f"  Month (numeric): {month}")
print(f"  Year: {year}")

print(f"\n✓ Constructed URL:")
print(f"  {url}")

print(f"\n✓ Expected selectors for slot extraction:")
print(f"  - data-day: '{day}'")
print(f"  - data-month: '{month_abbr}'")
print(f"  - CSS selector: button[data-day='{day}'][data-month='{month_abbr}']")

print(f"\n" + "=" * 60)
print("Testing Instructions")
print("=" * 60)

print(f"\n1. Manual Browser Test:")
print(f"   - Open the URL in your browser:")
print(f"     {url}")
print(f"   - Check if slots are displayed for {target_date}")
print(f"   - Open browser DevTools (F12)")
print(f"   - In Console, run:")
print(f"     document.querySelectorAll('button[data-day=\"{day}\"][data-month=\"{month_abbr}\"]')")
print(f"   - This should return the slot buttons")

print(f"\n2. Test via API (if Flask app is running):")
print(f"   curl -X POST http://localhost:5000/run_scraper \\")
print(f"     -H 'Content-Type: application/json' \\")
print(f"     -d '{{")
print(f'       "website": "swingers_nyc",')
print(f'       "guests": {guests},')
print(f'       "target_date": "{target_date}"')
print(f"     }}'")

print(f"\n3. Test Function Directly:")
print(f"   python test_swingers_nyc.py")

print(f"\n4. Check Database (after running scraper):")
print(f"   python -c \"")
print(f"from app import app, db, AvailabilitySlot")
print(f"from datetime import datetime")
print(f"with app.app_context():")
print(f"    slots = AvailabilitySlot.query.filter(")
print(f"        AvailabilitySlot.venue_name == 'Swingers (NYC)',")
print(f"        AvailabilitySlot.date == datetime.strptime('{target_date}', '%Y-%m-%d').date()")
print(f"    ).all()")
print(f"    print(f'Found {{len(slots)}} slots')")
print(f"    for slot in slots[:5]:")
print(f"        print(f'  - {{slot.time}}: {{slot.price}} ({{slot.status}})')")
print(f"   \"")

print(f"\n" + "=" * 60)
print("Quick Test Complete!")
print("=" * 60)

