"""
Test script for All Star Lanes Bowling scrapers
Tests all 4 London locations: Stratford, Holborn, White City, and Brick Lane
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

# Import the scraper functions
from scrapers.allstarlanes_bowling import (
    scrape_allstarlanes_Stratford,
    scrape_allstarlanes_Holborn,
    scrape_allstarlanes_White_city,
    scrape_allstarlanes_Brick_lane
)

def test_location(scraper_func, location_name, guests, target_date):
    """Test a single location scraper"""
    print(f"\n{'='*70}")
    print(f"Testing: {location_name}")
    print(f"Date: {target_date}, Guests: {guests}")
    print(f"{'='*70}")
    
    try:
        results = scraper_func(guests, target_date)
        
        if results:
            print(f"[SUCCESS] Found {len(results)} available slots")
            print("\n" + "="*70)
            print("ALL SLOT DETAILS:")
            print("="*70)
            
            for i, slot in enumerate(results, 1):
                print(f"\n--- Slot {i} of {len(results)} ---")
                print(f"  Date:           {slot.get('date', 'N/A')}")
                print(f"  Time:            {slot.get('time', 'N/A')}")
                print(f"  End Time:        {slot.get('end_time', 'N/A')}")
                print(f"  Availability:    {slot.get('availability', 'N/A')}")
                print(f"  Duration:        {slot.get('duration', 'N/A')}")
                print(f"  Guests:          {slot.get('guests', 'N/A')}")
                print(f"  Status:          {slot.get('status', 'N/A')}")
                print(f"  Website:         {slot.get('website', 'N/A')}")
                print(f"  Booking URL:     {slot.get('booking_url', 'N/A')}")
                print(f"  Timestamp:       {slot.get('timestamp', 'N/A')}")
            
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
    """Test all All Star Lanes locations"""
    # Test configuration
    TEST_GUESTS = 4
    TEST_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # 7 days from now
    
    print(f"\n{'#'*70}")
    print(f"TESTING ALL STAR LANES BOWLING - LONDON LOCATIONS")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*70}")
    
    # Define all locations to test
    locations = [
        (scrape_allstarlanes_Stratford, "All Star Lanes - Stratford"),
        (scrape_allstarlanes_Holborn, "All Star Lanes - Holborn"),
        (scrape_allstarlanes_White_city, "All Star Lanes - White City"),
        (scrape_allstarlanes_Brick_lane, "All Star Lanes - Brick Lane"),
    ]
    
    results_summary = []
    
    for scraper_func, location_name in locations:
        success, count = test_location(scraper_func, location_name, TEST_GUESTS, TEST_DATE)
        results_summary.append((location_name, success, count))
    
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
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {location}: {count} slots")
    
    return results_summary

def test_single_location(location_name, guests=4, days_ahead=7):
    """Test a single location by name"""
    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    location_map = {
        'stratford': (scrape_allstarlanes_Stratford, "All Star Lanes - Stratford"),
        'holborn': (scrape_allstarlanes_Holborn, "All Star Lanes - Holborn"),
        'white_city': (scrape_allstarlanes_White_city, "All Star Lanes - White City"),
        'white': (scrape_allstarlanes_White_city, "All Star Lanes - White City"),
        'brick_lane': (scrape_allstarlanes_Brick_lane, "All Star Lanes - Brick Lane"),
        'brick': (scrape_allstarlanes_Brick_lane, "All Star Lanes - Brick Lane"),
    }
    
    location_name_lower = location_name.lower().replace(' ', '_')
    
    if location_name_lower not in location_map:
        print(f"Unknown location: {location_name}")
        print(f"\nAvailable locations:")
        for key in location_map.keys():
            print(f"  - {key}")
        return
    
    scraper_func, display_name = location_map[location_name_lower]
    test_location(scraper_func, display_name, guests, target_date)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        location = sys.argv[1]
        guests = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        days_ahead = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        test_single_location(location, guests, days_ahead)
    else:
        # Default: Test all locations
        test_all_locations()
