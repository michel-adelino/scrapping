"""
Test script for Hijingo scraper
Tests the scrape_hijingo function with various configurations
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
from scrapers.hijingo import scrape_hijingo

def test_hijingo(guests, target_date):
    """Test the Hijingo scraper"""
    print(f"\n{'='*70}")
    print(f"Testing: Hijingo")
    print(f"Date: {target_date}, Guests: {guests}")
    print(f"{'='*70}")
    
    try:
        results = scrape_hijingo(guests, target_date)
        
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
                print(f"  Guests:         {slot.get('guests', 'N/A')}")
                if slot.get('description'):
                    print(f"  Description:    {slot.get('description', 'N/A')}")
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

def test_hijingo_multiple_dates():
    """Test Hijingo scraper with multiple dates"""
    TEST_GUESTS = 4
    TEST_DATES = [
        (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),   # 6 days from now
        (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),  # 12 days from now
        (datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d"),  # 18 days from now
    ]
    
    print(f"\n{'#'*70}")
    print(f"TESTING HIJINGO SCRAPER - MULTIPLE DATES")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*70}")
    
    results_summary = []
    
    for test_date in TEST_DATES:
        success, count = test_hijingo(TEST_GUESTS, test_date)
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

def test_hijingo_single(guests=4, days_ahead=7):
    """Test Hijingo scraper with a single date"""
    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    test_hijingo(guests, target_date)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Custom test: python test_hijingo.py [guests] [days_ahead]
        guests = int(sys.argv[1]) if len(sys.argv) > 1 else 4
        days_ahead = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        test_hijingo_single(guests, days_ahead)
    else:
        # Default: Test multiple dates
        test_hijingo_multiple_dates()
