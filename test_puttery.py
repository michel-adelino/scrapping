"""
Test script for Puttery scraper
Tests the scrape_puttery function with various configurations
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
from scrapers.puttery import scrape_puttery

def test_puttery(guests, target_date):
    """Test the Puttery scraper"""
    print(f"\n{'='*70}")
    print(f"Testing: Puttery (NYC)")
    print(f"Date: {target_date}, Guests: {guests}")
    print(f"{'='*70}")
    
    try:
        results = scrape_puttery(guests, target_date)
        
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
                if slot.get('booking_url'):
                    print(f"  Booking URL:    {slot.get('booking_url', 'N/A')}")
            
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

def test_puttery_multiple_dates():
    """Test Puttery scraper with multiple dates"""
    TEST_GUESTS = 3
    TEST_DATES = [
        (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),   # 7 days from now
        (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),  # 14 days from now
        (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d"),  # 21 days from now
    ]
    
    print(f"\n{'#'*70}")
    print(f"TESTING PUTTERY SCRAPER - MULTIPLE DATES")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*70}")
    
    results_summary = []
    
    for test_date in TEST_DATES:
        success, count = test_puttery(TEST_GUESTS, test_date)
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

def test_puttery_single(guests=3, days_ahead=7):
    """Test Puttery scraper with a single date"""
    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    test_puttery(guests, target_date)

def test_puttery_multiple_guests():
    """Test Puttery scraper with multiple guest counts"""
    TEST_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    TEST_GUESTS = [2, 3, 4, 5, 6]
    
    print(f"\n{'#'*70}")
    print(f"TESTING PUTTERY SCRAPER - MULTIPLE GUEST COUNTS")
    print(f"Test Date: {TEST_DATE}")
    print(f"{'#'*70}")
    
    results_summary = []
    
    for guests in TEST_GUESTS:
        print(f"\n--- Testing with {guests} guests ---")
        success, count = test_puttery(guests, TEST_DATE)
        results_summary.append((guests, success, count))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    successful = sum(1 for _, success, _ in results_summary if success)
    total = len(results_summary)
    total_slots = sum(count for _, _, count in results_summary)
    
    print(f"\nTotal Guest Counts Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Total Slots Found: {total_slots}")
    
    print("\nDetailed Results:")
    for guests, success, count in results_summary:
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {guests} guests: {count} slots")
    
    return results_summary

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'guests':
            # Test multiple guest counts: python test_puttery.py guests
            test_puttery_multiple_guests()
        else:
            # Custom test: python test_puttery.py [guests] [days_ahead]
            guests = int(sys.argv[1]) if len(sys.argv) > 1 else 3
            days_ahead = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            test_puttery_single(guests, days_ahead)
    else:
        # Default: Test multiple dates
        test_puttery_multiple_dates()
