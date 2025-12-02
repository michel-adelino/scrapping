#!/usr/bin/env python3
"""
Standalone test script for Swingers NYC scraper
No dependencies on app.py or other project files
"""

from datetime import datetime, timedelta
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from seleniumbase import Driver
import time

def test_swingers_nyc_scraper(guests=6, target_date=None):
    """
    Standalone test function for Swingers NYC scraper
    Tests the URL construction and slot extraction logic
    """
    # Use a date 30 days from now if not provided
    if not target_date:
        target_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        target_date = (datetime.now() + timedelta(days=31)).strftime("%Y-%m-%d")
        print(target_date,'>>><<')
    
    print("=" * 70)
    print("Standalone Swingers NYC Scraper Test")
    print("=" * 70)
    
    # Parse the target date
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        date_str = target_date
        month = dt.month
        year = dt.year
        day = dt.strftime("%d")
        month_abbr = dt.strftime("%b")
        
        print(f"\n✓ Date parsed successfully:")
        print(f"  - Target Date: {date_str}")
        print(f"  - Day: {day}")
        print(f"  - Month (abbr): {month_abbr}")
        print(f"  - Month (numeric): {month}")
        print(f"  - Year: {year}")
        print(f"  - Guests: {guests}")
        
    except ValueError as e:
        print(f"\n✗ Error parsing date: {e}")
        print(f"  Expected format: YYYY-MM-DD (e.g., 2025-11-30)")
        return False
    
    # Construct the URL with query parameters
    # Format: https://www.swingers.club/us/locations/nyc/book-now?guests=6&search%5Bmonth%5D=11&search%5Byear%5D=2025&depart=2025-11-30
    query_params = {
        'guests': str(guests),
        'search[month]': str(month),
        'search[year]': str(year),
        'depart': date_str
    }
    url = f"https://www.swingers.club/us/locations/nyc/book-now?{urlencode(query_params)}"
    
    print(f"\n✓ URL constructed:")
    print(f"  {url}")
    
    # Test URL construction
    print(f"\n✓ Expected selectors for slot extraction:")
    print(f"  - data-day: '{day}'")
    print(f"  - data-month: '{month_abbr}'")
    print(f"  - CSS selector: button[data-day='{day}'][data-month='{month_abbr}']")
    
    # Ask user if they want to run the actual scraper
    print(f"\n" + "=" * 70)
    print("Ready to test scraper")
    print("=" * 70)
    print(f"\nThis will:")
    print(f"  1. Open a browser (headless)")
    print(f"  2. Navigate to the URL")
    print(f"  3. Wait for slots to load")
    print(f"  4. Extract and display available slots")
    print(f"\nPress Enter to continue, or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        return False
    
    # Run the actual scraper
    driver = None
    try:
        print(f"\n" + "=" * 70)
        print("Starting browser and navigating to URL...")
        print("=" * 70)
        
        # driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver = Driver(        
            uc=False,        
            headless2=False, # server-safe true headless        
            no_sandbox=True,        
            disable_gpu=True,        
            headed=True,        
        )
        print(f"✓ Browser started")
        
        print(f"✓ Navigating to: {url}")
        driver.get(url)
        print(f"✓ Page loaded")
        
        # Wait for page to load and slots to appear
        print(f"✓ Waiting for slots to load...")
        try:
            # Wait for any slot button to appear (indicating slots are loaded)
            driver.wait_for_element('button[data-day][data-month]', timeout=10)
            print(f"✓ Slots detected on page")
        except:
            # If wait fails, just sleep and continue
            print(f"⚠ Wait for elements timed out, continuing anyway...")
            driver.sleep(5)
        
        # Parse the page and find available slots
        print(f"\n" + "=" * 70)
        print("Extracting slots from page...")
        print("=" * 70)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all("button", {"data-day": day, "data-month": month_abbr})
        
        print(f"✓ Found {len(slots)} slot buttons matching criteria")
        print(f"  (data-day='{day}', data-month='{month_abbr}')")
        
        if len(slots) == 0:
            print(f"\n⚠ No slots found with the expected selectors")
            print(f"\nDebugging information:")
            print(f"  - Checking for any slot buttons on the page...")
            
            # Check for any slot buttons
            all_slot_buttons = soup.find_all("button", {"data-day": True, "data-month": True})
            print(f"  - Found {len(all_slot_buttons)} total slot buttons with data-day and data-month attributes")
            
            if len(all_slot_buttons) > 0:
                print(f"\n  Sample slot buttons found:")
                for i, btn in enumerate(all_slot_buttons[:5], 1):
                    btn_day = btn.get("data-day", "N/A")
                    btn_month = btn.get("data-month", "N/A")
                    print(f"    {i}. data-day='{btn_day}', data-month='{btn_month}'")
                
                print(f"\n  Expected: data-day='{day}', data-month='{month_abbr}'")
                print(f"\n  ⚠ Mismatch detected! The selectors might need adjustment.")
            
            # Check page source for debugging
            print(f"\n  Saving page source to 'swingers_page_source.html' for inspection...")
            with open('swingers_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"  ✓ Page source saved")
            
            return False
        
        # Extract slot information
        print(f"\n" + "=" * 70)
        print("Extracted Slots:")
        print("=" * 70)
        
        slots_data = []
        for i, slot in enumerate(slots, 1):
            # Status
            status_el = slot.select_one("div.slot-search-result__low-stock")
            if status_el:
                status = status_el.get_text(strip=True)
            else:
                status = "Available"
            
            # Time
            try:
                time_el = slot.find("span", {"class": "slot-search-result__time h5"})
                time_str = time_el.get_text().strip() if time_el else "None"
            except:
                time_str = "None"
            
            # Price
            try:
                price_el = slot.find("span", {"class": "slot-search-result__price-label"})
                price = price_el.get_text().strip() if price_el else "None"
            except:
                price = "None"
            
            slots_data.append({
                'time': time_str,
                'price': price,
                'status': status
            })
            
            print(f"\n  Slot {i}:")
            print(f"    Time: {time_str}")
            print(f"    Price: {price}")
            print(f"    Status: {status}")
        
        print(f"\n" + "=" * 70)
        print("Test Results")
        print("=" * 70)
        print(f"✓ Successfully extracted {len(slots_data)} slots")
        print(f"✓ Date: {date_str}")
        print(f"✓ Guests: {guests}")
        print(f"✓ URL: {url}")
        
        # Summary
        available_count = sum(1 for s in slots_data if s['status'] == "Available")
        low_stock_count = len(slots_data) - available_count
        
        print(f"\nSummary:")
        print(f"  - Total slots: {len(slots_data)}")
        print(f"  - Available: {available_count}")
        print(f"  - Low stock: {low_stock_count}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            print(f"\n✓ Closing browser...")
            driver.quit()
            print(f"✓ Browser closed")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    guests = 6
    target_date = None
    
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    if len(sys.argv) > 2:
        guests = int(sys.argv[2])
    
    # Run the test
    success = test_swingers_nyc_scraper(guests=guests, target_date=target_date)
    
    if success:
        print(f"\n" + "=" * 70)
        print("✓ Test completed successfully!")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"\n" + "=" * 70)
        print("✗ Test completed with issues")
        print("=" * 70)
        sys.exit(1)

