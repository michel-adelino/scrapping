"""
Test script to test all Celery tasks for verification in the backend project
Tests the actual tasks that run in production (scrape_venue_task)
"""
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import Flask app and create app context
from app import app, scrape_venue_task, NYC_VENUES, LONDON_VENUES

# Test configuration
TEST_GUESTS = 6
TEST_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # 7 days from now

def test_venue_task(website, guests, target_date, **kwargs):
    """Test a single scrape_venue_task"""
    print(f"\n{'='*60}")
    print(f"Testing: {website}")
    print(f"Date: {target_date}, Guests: {guests}")
    print(f"{'='*60}")
    
    try:
        # Call the task's .run() method directly to bypass Celery's wrapper
        # For bound tasks, .run() takes the arguments without 'self'
        with app.app_context():
            result = scrape_venue_task.run(guests, target_date, website, **kwargs)
        
        if result:
            slots_found = result.get("slots_found", 0) if isinstance(result, dict) else 0
            if slots_found > 0:
                print(f"✓ SUCCESS: Found {slots_found} slots")
                # Show first 3 slots as sample if available
                slots = result.get("slots", [])
                if slots:
                    for i, slot in enumerate(slots[:3], 1):
                        venue = slot.get('website', slot.get('venue_name', 'N/A'))
                        time = slot.get('time', 'N/A')
                        status = slot.get('status', 'N/A')
                        price = slot.get('price', 'N/A')
                        print(f"  Sample {i}: {venue} - {time} - {status} - {price}")
                    if len(slots) > 3:
                        print(f"  ... and {len(slots) - 3} more slots")
            else:
                print(f"⚠ WARNING: No slots found (this might be normal if no availability)")
            return True, slots_found
        else:
            print(f"⚠ WARNING: Task returned no result")
            return True, 0
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_all_venues():
    """Test all venues using scrape_venue_task (matches production task structure)"""
    print(f"\n{'#'*60}")
    print(f"TESTING ALL VENUE TASKS (Production Task Structure)")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"Total Venues: {len(NYC_VENUES) + len(LONDON_VENUES)}")
    print(f"{'#'*60}\n")
    
    results_summary = []
    
    # NYC Venues
    print("\n" + "="*60)
    print("NYC VENUES")
    print("="*60)
    
    for venue in NYC_VENUES:
        success, count = test_venue_task(venue, TEST_GUESTS, TEST_DATE)
        results_summary.append((venue, success, count))
    
    # London Venues
    print("\n" + "="*60)
    print("LONDON VENUES")
    print("="*60)
    
    # For venues that need location parameters
    london_venue_params = {
        'clays_bar': {'clays_location': 'Canary Wharf'},
        'puttshack': {'puttshack_location': 'Bank'},
        'f1_arcade': {'f1_experience': 'Team Racing'},
    }
    
    for venue in LONDON_VENUES:
        params = london_venue_params.get(venue, {})
        success, count = test_venue_task(venue, TEST_GUESTS, TEST_DATE, **params)
        results_summary.append((venue, success, count))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for _, success, _ in results_summary if success)
    total = len(results_summary)
    total_slots = sum(count for _, _, count in results_summary)
    
    print(f"\nTotal Venues Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Total Slots Found: {total_slots}")
    
    print("\nDetailed Results:")
    for venue, success, count in results_summary:
        status = "✓" if success else "✗"
        print(f"  {status} {venue}: {count} slots")
    
    return results_summary

def test_single_venue(venue_name):
    """Test a single venue by name"""
    # Check if it's a valid venue
    all_venues = NYC_VENUES + LONDON_VENUES
    if venue_name not in all_venues:
        print(f"Unknown venue: {venue_name}")
        print(f"\nAvailable NYC venues:")
        for v in NYC_VENUES:
            print(f"  - {v}")
        print(f"\nAvailable London venues:")
        for v in LONDON_VENUES:
            print(f"  - {v}")
        return
    
    # Set location parameters for venues that need them
    params = {}
    if venue_name == 'clays_bar':
        params = {'clays_location': 'Canary Wharf'}
    elif venue_name == 'puttshack':
        params = {'puttshack_location': 'Bank'}
    elif venue_name == 'f1_arcade':
        params = {'f1_experience': 'Team Racing'}
    
    test_venue_task(venue_name, TEST_GUESTS, TEST_DATE, **params)

def test_all_five_iron_golf_locations():
    """Test all Five Iron Golf NYC locations"""
    print(f"\n{'#'*60}")
    print(f"TESTING ALL FIVE IRON GOLF NYC LOCATIONS")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*60}\n")
    
    five_iron_venues = [v for v in NYC_VENUES if v.startswith('five_iron_golf_nyc_')]
    
    results = []
    for venue in five_iron_venues:
        success, count = test_venue_task(venue, TEST_GUESTS, TEST_DATE)
        results.append((venue, success, count))
    
    print(f"\n{'='*60}")
    print("FIVE IRON GOLF SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for _, success, _ in results if success)
    total_slots = sum(count for _, _, count in results)
    print(f"Locations Tested: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Total Slots Found: {total_slots}")

def test_all_lawn_club_options():
    """Test all Lawn Club NYC options"""
    print(f"\n{'#'*60}")
    print(f"TESTING ALL LAWN CLUB NYC OPTIONS")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*60}\n")
    
    lawn_club_venues = [v for v in NYC_VENUES if v.startswith('lawn_club_nyc_')]
    
    results = []
    for venue in lawn_club_venues:
        success, count = test_venue_task(venue, TEST_GUESTS, TEST_DATE)
        results.append((venue, success, count))
    
    print(f"\n{'='*60}")
    print("LAWN CLUB SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for _, success, _ in results if success)
    total_slots = sum(count for _, _, count in results)
    print(f"Options Tested: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Total Slots Found: {total_slots}")

def test_flight_club_darts_all_locations():
    """Test Flight Club Darts (should return slots for all 4 locations)"""
    print(f"\n{'#'*60}")
    print(f"TESTING FLIGHT CLUB DARTS (All 4 Locations)")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*60}\n")
    
    success, count = test_venue_task('flight_club_darts', TEST_GUESTS, TEST_DATE)
    
    print(f"\n{'='*60}")
    print("FLIGHT CLUB DARTS SUMMARY")
    print(f"{'='*60}")
    print(f"Status: {'✓ SUCCESS' if success else '✗ FAILED'}")
    print(f"Total Slots Found: {count}")
    print(f"Note: This single task should return slots for all 4 locations")
    print(f"      (Bloomsbury, Angel, Shoreditch, Victoria)")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'all':
            # Test all venues
            test_all_venues()
        elif command == 'five_iron':
            # Test all Five Iron Golf locations
            test_all_five_iron_golf_locations()
        elif command == 'lawn_club':
            # Test all Lawn Club options
            test_all_lawn_club_options()
        elif command == 'flight_club':
            # Test Flight Club Darts
            test_flight_club_darts_all_locations()
        else:
            # Test single venue
            test_single_venue(command)
    else:
        # Default: Test all venues
        test_all_venues()
