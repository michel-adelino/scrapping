"""
Test script for SPIN scraper
Tests both NYC locations: Flatiron and Midtown
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Configure logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import the scraper function
from scrapers.spin import scrape_spin, SPIN_VENUE_NAMES

def test_spin_location(location, guests, target_date, selected_time=None):
    """Test the SPIN scraper for a specific location"""
    location_name = SPIN_VENUE_NAMES.get(location, f'SPIN (NYC - {location.title()})')
    
    print(f"\n{'='*70}")
    print(f"Testing: {location_name}")
    print(f"Location: {location}")
    print(f"Date: {target_date}, Guests: {guests}")
    if selected_time:
        print(f"Selected Time: {selected_time}")
    print(f"{'='*70}")
    
    try:
        results = scrape_spin(guests, target_date, selected_time, location)
        
        if results:
            print(f"[SUCCESS] Found {len(results)} available slots")
            print("\n" + "="*70)
            print("ALL SLOT DETAILS:")
            print("="*70)
            
            for i, slot in enumerate(results, 1):
                print(f"\n--- Slot {i} of {len(results)} ---")
                print(f"  Date:           {slot.get('date', 'N/A')}")
                print(f"  Time:           {slot.get('time', 'N/A')}")
                print(f"  Price:          {slot.get('price', 'N/A')}")
                print(f"  Status:         {slot.get('status', 'N/A')}")
                print(f"  Website:        {slot.get('website', 'N/A')}")
                print(f"  Timestamp:      {slot.get('timestamp', 'N/A')}")
            
            print("\n" + "="*70)
            return True, len(results)
        else:
            print("[WARNING] No slots found (this might be normal if no availability)")
            return True, 0
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_all_locations():
    """Test all SPIN locations"""
    # Test configuration
    TEST_GUESTS = 4
    TEST_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # 7 days from now
    
    print(f"\n{'#'*70}")
    print(f"TESTING SPIN - NYC LOCATIONS")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*70}")
    
    # Define all locations to test
    locations = ['flatiron', 'midtown']
    
    results_summary = []
    
    for location in locations:
        success, count = test_spin_location(location, TEST_GUESTS, TEST_DATE)
        results_summary.append((location, success, count))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    successful = sum(1 for _, success, _ in results_summary if success)
    total = len(results_summary)
    total_slots = sum(count for _, _, count in results_summary)
    
    print(f"\nTotal Locations Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Total Slots Found: {total_slots}")
    
    print("\nDetailed Results:")
    for location, success, count in results_summary:
        location_name = SPIN_VENUE_NAMES.get(location, location)
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {location_name}: {count} slots")
    
    return results_summary

def test_spin_multiple_dates(location='flatiron'):
    """Test SPIN scraper with multiple dates for a specific location"""
    TEST_GUESTS = 4
    TEST_DATES = [
        (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),   # 6 days from now
        (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),  # 12 days from now
        (datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d"),  # 18 days from now
    ]
    
    location_name = SPIN_VENUE_NAMES.get(location, f'SPIN (NYC - {location.title()})')
    
    print(f"\n{'#'*70}")
    print(f"TESTING SPIN SCRAPER - MULTIPLE DATES")
    print(f"Location: {location_name}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*70}")
    
    results_summary = []
    
    for test_date in TEST_DATES:
        success, count = test_spin_location(location, TEST_GUESTS, test_date)
        results_summary.append((test_date, success, count))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    successful = sum(1 for _, success, _ in results_summary if success)
    total = len(results_summary)
    total_slots = sum(count for _, _, count in results_summary)
    
    print(f"\nTotal Dates Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Total Slots Found: {total_slots}")
    
    print("\nDetailed Results:")
    for date, success, count in results_summary:
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {date}: {count} slots")
    
    return results_summary

def test_spin_single(location='flatiron', guests=4, days_ahead=7, selected_time=None):
    """Test SPIN scraper with a single date"""
    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    test_spin_location(location, guests, target_date, selected_time)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Custom test: python test_spin.py [location] [guests] [days_ahead] [selected_time]
        location = sys.argv[1] if len(sys.argv) > 1 else 'flatiron'
        guests = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        days_ahead = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        selected_time = sys.argv[4] if len(sys.argv) > 4 else None
        
        # Validate location
        if location not in SPIN_VENUE_NAMES:
            print(f"Unknown location: {location}")
            print(f"\nAvailable locations:")
            for loc in SPIN_VENUE_NAMES.keys():
                print(f"  - {loc}")
            sys.exit(1)
        
        test_spin_single(location, guests, days_ahead, selected_time)
    else:
        # Default: Test all locations
        test_all_locations()
