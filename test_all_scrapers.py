"""
Test script to run each scraper script once to verify they're working correctly.
Tests the actual scraper functions directly (not through Celery tasks).

Usage:
    # Test all scrapers
    python test_all_scrapers.py
    python test_all_scrapers.py all
    
    # Test a single scraper
    python test_all_scrapers.py swingers_nyc
    python test_all_scrapers.py clays_bar
    python test_all_scrapers.py daysmart_chelsea
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Test configuration
TEST_GUESTS = 4
TEST_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # 7 days from now

def test_scraper(scraper_name, scraper_func):
    """Test a single scraper function"""
    print(f"\n{'='*70}")
    print(f"Testing: {scraper_name}")
    print(f"Date: {TEST_DATE}, Guests: {TEST_GUESTS}")
    print(f"{'='*70}")
    
    try:
        # Call the scraper function (it's a lambda that already has all params)
        results = scraper_func()
        
        if results is None:
            print(f"⚠ WARNING: Scraper returned None")
            return True, 0
        elif isinstance(results, list):
            if len(results) > 0:
                print(f"✓ SUCCESS: Found {len(results)} slots")
                # Show first 3 slots as sample
                for i, slot in enumerate(results[:3], 1):
                    venue = slot.get('website', slot.get('venue_name', 'N/A'))
                    time = slot.get('time', 'N/A')
                    status = slot.get('status', 'N/A')
                    price = slot.get('price', 'N/A')
                    print(f"  Sample {i}: {venue} - {time} - {status} - {price}")
                if len(results) > 3:
                    print(f"  ... and {len(results) - 3} more slots")
                return True, len(results)
            else:
                print(f"⚠ WARNING: No slots found (this might be normal if no availability)")
                return True, 0
        else:
            print(f"⚠ WARNING: Unexpected return type: {type(results)}")
            return True, 0
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_all_scrapers():
    """Test all scraper functions"""
    print(f"\n{'#'*70}")
    print(f"TESTING ALL SCRAPER FUNCTIONS")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Guests: {TEST_GUESTS}")
    print(f"{'#'*70}")
    
    results_summary = []
    
    # Import all scrapers
    try:
        from scrapers import swingers
        from scrapers import electric_shuffle
        from scrapers import lawn_club
        from scrapers import spin
        from scrapers import five_iron_golf
        from scrapers import lucky_strike
        from scrapers import easybowl
        from scrapers import tsquaredsocial
        from scrapers import daysmart
        from scrapers import fair_game
        from scrapers import clays_bar
        from scrapers import puttshack
        from scrapers import flight_club_darts
        from scrapers import f1_arcade
        from scrapers import topgolfchigwell
        from scrapers import hijingo
        from scrapers import pingpong
        from scrapers import puttery
        from scrapers import allstarlanes_bowling
    except ImportError as e:
        print(f"✗ ERROR: Failed to import scrapers: {e}")
        return []
    
    # Define all scrapers to test with their function calls
    scrapers_to_test = [
        # NYC Venues
        ("Swingers NYC", lambda: swingers.scrape_swingers(TEST_GUESTS, TEST_DATE)),
        ("Electric Shuffle NYC", lambda: electric_shuffle.scrape_electric_shuffle(TEST_GUESTS, TEST_DATE)),
        ("Lawn Club NYC - Indoor Gaming", lambda: lawn_club.scrape_lawn_club(TEST_GUESTS, TEST_DATE, option='indoor_gaming')),
        ("Lawn Club NYC - Curling Lawns", lambda: lawn_club.scrape_lawn_club(TEST_GUESTS, TEST_DATE, option='curling_lawns')),
        ("Lawn Club NYC - Croquet Lawns", lambda: lawn_club.scrape_lawn_club(TEST_GUESTS, TEST_DATE, option='croquet_lawns')),
        ("SPIN NYC", lambda: spin.scrape_spin(TEST_GUESTS, TEST_DATE)),
        ("Five Iron Golf - FiDi", lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='fidi')),
        ("Five Iron Golf - Flatiron", lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='flatiron')),
        ("Five Iron Golf - Grand Central", lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='grand_central')),
        ("Five Iron Golf - Herald Square", lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='herald_square')),
        ("Five Iron Golf - Long Island City", lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='long_island_city')),
        ("Five Iron Golf - Upper East Side", lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='upper_east_side')),
        ("Five Iron Golf - Rockefeller Center", lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='rockefeller_center')),
        ("Lucky Strike NYC", lambda: lucky_strike.scrape_lucky_strike(TEST_GUESTS, TEST_DATE)),
        ("Easybowl NYC", lambda: easybowl.scrape_easybowl(TEST_GUESTS, TEST_DATE)),
        ("T-Squared Social NYC", lambda: tsquaredsocial.scrape_tsquaredsocial(TEST_GUESTS, TEST_DATE)),
        ("Chelsea Piers Golf (DaySmart)", lambda: daysmart.scrape_daysmart_chelsea(TEST_DATE)),  # Only supports 2 guests, but we'll test the function
        
        # London Venues
        ("Swingers London", lambda: swingers.scrape_swingers_uk(TEST_GUESTS, TEST_DATE)),
        ("Electric Shuffle London", lambda: electric_shuffle.scrape_electric_shuffle_london(TEST_GUESTS, TEST_DATE)),
        ("Fair Game - Canary Wharf", lambda: fair_game.scrape_fair_game_canary_wharf(TEST_GUESTS, TEST_DATE)),
        ("Fair Game - City", lambda: fair_game.scrape_fair_game_city(TEST_GUESTS, TEST_DATE)),
        ("Clays Bar - Canary Wharf", lambda: clays_bar.scrape_clays_bar('Canary Wharf', TEST_GUESTS, TEST_DATE)),
        ("Puttshack - Bank", lambda: puttshack.scrape_puttshack('Bank', TEST_GUESTS, TEST_DATE)),
        ("Flight Club Darts (All Locations)", lambda: flight_club_darts.scrape_flight_club_darts(TEST_GUESTS, TEST_DATE)),
        ("F1 Arcade - Team Racing", lambda: f1_arcade.scrape_f1_arcade(TEST_GUESTS, TEST_DATE, f1_experience='Team Racing')),
        ("Topgolf Chigwell", lambda: topgolfchigwell.scrape_topgolf_chigwell(TEST_GUESTS, TEST_DATE)),
        ("Hijingo", lambda: hijingo.scrape_hijingo(TEST_GUESTS, TEST_DATE)),
        ("Ping Pong", lambda: pingpong.scrape_pingpong(TEST_GUESTS, TEST_DATE)),
        ("Puttery", lambda: puttery.scrape_puttery(TEST_GUESTS, TEST_DATE)),
        ("All Star Lanes - Stratford", lambda: allstarlanes_bowling.scrape_allstarlanes_Stratford(TEST_GUESTS, TEST_DATE)),
        ("All Star Lanes - Holborn", lambda: allstarlanes_bowling.scrape_allstarlanes_Holborn(TEST_GUESTS, TEST_DATE)),
        ("All Star Lanes - White City", lambda: allstarlanes_bowling.scrape_allstarlanes_White_city(TEST_GUESTS, TEST_DATE)),
        ("All Star Lanes - Brick Lane", lambda: allstarlanes_bowling.scrape_allstarlanes_Brick_lane(TEST_GUESTS, TEST_DATE)),
    ]
    
    # Run tests
    for scraper_name, scraper_func in scrapers_to_test:
        success, count = test_scraper(scraper_name, scraper_func)
        results_summary.append((scraper_name, success, count))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    successful = sum(1 for _, success, _ in results_summary if success)
    total = len(results_summary)
    total_slots = sum(count for _, _, count in results_summary)
    failed = total - successful
    
    print(f"\nTotal Scrapers Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total Slots Found: {total_slots}")
    
    print("\nDetailed Results:")
    for scraper_name, success, count in results_summary:
        status = "✓" if success else "✗"
        print(f"  {status} {scraper_name}: {count} slots")
    
    # Show failed scrapers if any
    if failed > 0:
        print("\nFailed Scrapers:")
        for scraper_name, success, count in results_summary:
            if not success:
                print(f"  ✗ {scraper_name}")
    
    return results_summary

def test_single_scraper(scraper_name):
    """Test a single scraper by name"""
    scraper_map = {
        # NYC
        'swingers_nyc': ('Swingers NYC', lambda: swingers.scrape_swingers(TEST_GUESTS, TEST_DATE)),
        'electric_shuffle_nyc': ('Electric Shuffle NYC', lambda: electric_shuffle.scrape_electric_shuffle(TEST_GUESTS, TEST_DATE)),
        'lawn_club_indoor': ('Lawn Club NYC - Indoor Gaming', lambda: lawn_club.scrape_lawn_club(TEST_GUESTS, TEST_DATE, option='indoor_gaming')),
        'lawn_club_curling': ('Lawn Club NYC - Curling Lawns', lambda: lawn_club.scrape_lawn_club(TEST_GUESTS, TEST_DATE, option='curling_lawns')),
        'lawn_club_croquet': ('Lawn Club NYC - Croquet Lawns', lambda: lawn_club.scrape_lawn_club(TEST_GUESTS, TEST_DATE, option='croquet_lawns')),
        'spin_nyc': ('SPIN NYC', lambda: spin.scrape_spin(TEST_GUESTS, TEST_DATE)),
        'five_iron_fidi': ('Five Iron Golf - FiDi', lambda: five_iron_golf.scrape_five_iron_golf(TEST_GUESTS, TEST_DATE, location='fidi')),
        'lucky_strike_nyc': ('Lucky Strike NYC', lambda: lucky_strike.scrape_lucky_strike(TEST_GUESTS, TEST_DATE)),
        'easybowl_nyc': ('Easybowl NYC', lambda: easybowl.scrape_easybowl(TEST_GUESTS, TEST_DATE)),
        'tsquaredsocial_nyc': ('T-Squared Social NYC', lambda: tsquaredsocial.scrape_tsquaredsocial(TEST_GUESTS, TEST_DATE)),
        'daysmart_chelsea': ('Chelsea Piers Golf', lambda: daysmart.scrape_daysmart_chelsea(TEST_DATE)),
        
        # London
        'swingers_london': ('Swingers London', lambda: swingers.scrape_swingers_uk(TEST_GUESTS, TEST_DATE)),
        'electric_shuffle_london': ('Electric Shuffle London', lambda: electric_shuffle.scrape_electric_shuffle_london(TEST_GUESTS, TEST_DATE)),
        'fair_game_canary': ('Fair Game - Canary Wharf', lambda: fair_game.scrape_fair_game_canary_wharf(TEST_GUESTS, TEST_DATE)),
        'fair_game_city': ('Fair Game - City', lambda: fair_game.scrape_fair_game_city(TEST_GUESTS, TEST_DATE)),
        'clays_bar': ('Clays Bar - Canary Wharf', lambda: clays_bar.scrape_clays_bar('Canary Wharf', TEST_GUESTS, TEST_DATE)),
        'puttshack': ('Puttshack - Bank', lambda: puttshack.scrape_puttshack('Bank', TEST_GUESTS, TEST_DATE)),
        'flight_club_darts': ('Flight Club Darts', lambda: flight_club_darts.scrape_flight_club_darts(TEST_GUESTS, TEST_DATE)),
        'f1_arcade': ('F1 Arcade', lambda: f1_arcade.scrape_f1_arcade(TEST_GUESTS, TEST_DATE, f1_experience='Team Racing')),
        'topgolf_chigwell': ('Topgolf Chigwell', lambda: topgolfchigwell.scrape_topgolf_chigwell(TEST_GUESTS, TEST_DATE)),
        'hijingo': ('Hijingo', lambda: hijingo.scrape_hijingo(TEST_GUESTS, TEST_DATE)),
        'pingpong': ('Ping Pong', lambda: pingpong.scrape_pingpong(TEST_GUESTS, TEST_DATE)),
        'puttery': ('Puttery', lambda: puttery.scrape_puttery(TEST_GUESTS, TEST_DATE)),
        'allstarlanes_stratford': ('All Star Lanes - Stratford', lambda: allstarlanes_bowling.scrape_allstarlanes_Stratford(TEST_GUESTS, TEST_DATE)),
        'allstarlanes_holborn': ('All Star Lanes - Holborn', lambda: allstarlanes_bowling.scrape_allstarlanes_Holborn(TEST_GUESTS, TEST_DATE)),
        'allstarlanes_white_city': ('All Star Lanes - White City', lambda: allstarlanes_bowling.scrape_allstarlanes_White_city(TEST_GUESTS, TEST_DATE)),
        'allstarlanes_brick_lane': ('All Star Lanes - Brick Lane', lambda: allstarlanes_bowling.scrape_allstarlanes_Brick_lane(TEST_GUESTS, TEST_DATE)),
    }
    
    # Import scrapers
    from scrapers import swingers, electric_shuffle, lawn_club, spin, five_iron_golf
    from scrapers import lucky_strike, easybowl, tsquaredsocial, daysmart, fair_game
    from scrapers import clays_bar, puttshack, flight_club_darts, f1_arcade, topgolfchigwell
    from scrapers import hijingo, pingpong, puttery, allstarlanes_bowling
    
    scraper_name_lower = scraper_name.lower().replace(' ', '_')
    
    if scraper_name_lower not in scraper_map:
        print(f"Unknown scraper: {scraper_name}")
        print(f"\nAvailable scrapers:")
        for key in scraper_map.keys():
            print(f"  - {key}")
        return
    
    display_name, scraper_func = scraper_map[scraper_name_lower]
    test_scraper(display_name, scraper_func)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'all':
            test_all_scrapers()
        else:
            test_single_scraper(command)
    else:
        # Default: Test all scrapers
        test_all_scrapers()
