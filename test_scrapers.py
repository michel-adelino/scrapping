"""
Test script to run all scrapers once for verification in the scrapping project
"""
import sys
import os
from datetime import datetime, timedelta

# Add the scrapping directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app module to access scraper functions
import app

# Test configuration
TEST_GUESTS = 6
TEST_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # 7 days from now

def reset_scraping_state():
    """Reset global scraping state before each test"""
    app.scraping_status = {
        'running': False,
        'progress': 'Ready',
        'completed': False,
        'error': None,
        'total_slots_found': 0,
        'current_date': None,
        'website': None
    }
    app.scraped_data = []

def test_scraper(scraper_func, name, *args, **kwargs):
    """Test a single scraper function"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Date: {TEST_DATE}, Guests: {TEST_GUESTS}")
    print(f"{'='*60}")
    
    # Reset state before each test
    reset_scraping_state()
    
    try:
        # Call the scraper function
        scraper_func(*args, **kwargs)
        
        # Check results from global scraped_data
        results = app.scraped_data.copy()
        status = app.scraping_status
        
        if status.get('error'):
            print(f"✗ ERROR: {status.get('error')}")
            return False, 0
        
        if results:
            print(f"✓ SUCCESS: Found {len(results)} slots")
            print(f"  Progress: {status.get('progress', 'N/A')}")
            # Show first 3 results as sample
            for i, slot in enumerate(results[:3], 1):
                print(f"  Sample {i}: {slot.get('time', 'N/A')} - {slot.get('status', 'N/A')} - {slot.get('price', 'N/A')}")
            if len(results) > 3:
                print(f"  ... and {len(results) - 3} more slots")
        else:
            print(f"⚠ WARNING: No slots found")
            print(f"  Progress: {status.get('progress', 'N/A')}")
            if status.get('progress') and 'No' in status.get('progress', ''):
                print(f"  (This might be normal if no availability)")
        
        return True, len(results)
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_all_scrapers():
    """Test all scrapers in sequence"""
    print(f"\n{'#'*60}")
    print(f"TESTING ALL SCRAPERS (Selenium-based)")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*60}\n")
    
    results_summary = []
    
    # NYC Scrapers - using scrape_restaurants as wrapper
    print("\n" + "="*60)
    print("NYC SCRAPERS")
    print("="*60)
    
    nyc_test_cases = [
        # (website, name, **kwargs)
        ('swingers_nyc', "Swingers NYC", {}),
        ('electric_shuffle_nyc', "Electric Shuffle NYC", {}),
        ('lawn_club_nyc', "Lawn Club NYC", {'lawn_club_option': "Curling Lawns & Cabins"}),
        ('spin_nyc', "SPIN NYC", {}),
        ('five_iron_golf_nyc', "Five Iron Golf NYC", {}),
        ('lucky_strike_nyc', "Lucky Strike NYC", {}),
        ('easybowl_nyc', "Easybowl NYC", {}),
    ]
    
    for website, name, kwargs in nyc_test_cases:
        def test_wrapper(w=website, k=kwargs):
            app.scrape_restaurants(TEST_GUESTS, TEST_DATE, w, **k)
        success, count = test_scraper(test_wrapper, name)
        results_summary.append((name, success, count))
    
    # London Scrapers
    print("\n" + "="*60)
    print("LONDON SCRAPERS")
    print("="*60)
    
    london_test_cases = [
        ('swingers_london', "Swingers London", {}),
        ('electric_shuffle_london', "Electric Shuffle London", {}),
        ('fair_game_canary_wharf', "Fair Game Canary Wharf", {}),
        ('fair_game_city', "Fair Game City", {}),
        ('clays_bar', "Clays Bar", {'clays_location': "Canary Wharf"}),
        ('puttshack', "Puttshack", {'puttshack_location': "Bank"}),
        ('flight_club_darts', "Flight Club Darts (Bloomsbury)", {}),
        ('f1_arcade', "F1 Arcade", {'f1_experience': "Team Racing"}),
    ]
    
    for website, name, kwargs in london_test_cases:
        def test_wrapper(w=website, k=kwargs):
            app.scrape_restaurants(TEST_GUESTS, TEST_DATE, w, **k)
        success, count = test_scraper(test_wrapper, name)
        results_summary.append((name, success, count))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for _, success, _ in results_summary if success)
    total = len(results_summary)
    total_slots = sum(count for _, _, count in results_summary)
    
    print(f"\nTotal Scrapers Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Total Slots Found: {total_slots}")
    
    print("\nDetailed Results:")
    for name, success, count in results_summary:
        status = "✓" if success else "✗"
        print(f"  {status} {name}: {count} slots")
    
    return results_summary

def test_single_scraper(scraper_name):
    """Test a single scraper by name"""
    scraper_map = {
        'swingers_nyc': ("Swingers NYC", {}),
        'swingers_london': ("Swingers London", {}),
        'electric_shuffle_nyc': ("Electric Shuffle NYC", {}),
        'electric_shuffle_london': ("Electric Shuffle London", {}),
        'lawn_club_nyc': ("Lawn Club NYC", {'lawn_club_option': "Curling Lawns & Cabins"}),
        'spin_nyc': ("SPIN NYC", {}),
        'five_iron_golf_nyc': ("Five Iron Golf NYC", {}),
        'lucky_strike_nyc': ("Lucky Strike NYC", {}),
        'easybowl_nyc': ("Easybowl NYC", {}),
        'fair_game_canary_wharf': ("Fair Game Canary Wharf", {}),
        'fair_game_city': ("Fair Game City", {}),
        'clays_bar': ("Clays Bar", {'clays_location': "Canary Wharf"}),
        'puttshack': ("Puttshack", {'puttshack_location': "Bank"}),
        'flight_club_darts': ("Flight Club Darts (Bloomsbury)", {}),
        'f1_arcade': ("F1 Arcade", {'f1_experience': "Team Racing"}),
    }
    
    if scraper_name not in scraper_map:
        print(f"Unknown scraper: {scraper_name}")
        print(f"Available scrapers: {', '.join(scraper_map.keys())}")
        return
    
    name, kwargs = scraper_map[scraper_name]
    def test_wrapper(sn=scraper_name, k=kwargs):
        app.scrape_restaurants(TEST_GUESTS, TEST_DATE, sn, **k)
    test_scraper(test_wrapper, name)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Test single scraper
        scraper_name = sys.argv[1]
        test_single_scraper(scraper_name)
    else:
        # Test all scrapers
        test_all_scrapers()

