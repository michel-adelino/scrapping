#!/usr/bin/env python3
"""
Standalone test script for Swingers NYC scraper
No dependencies on app.py or other project files
"""

from datetime import datetime, timedelta
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
    
    # Construct the base URL (matching original working code)
    # Original code uses: https://www.swingers.club/us/locations/nyc/book-now?guests={guests}
    base_url = f"https://www.swingers.club/us/locations/nyc/book-now?guests={str(guests)}"
    
    print(f"\n✓ Base URL constructed (matching original working code):")
    print(f"  {base_url}")
    
    print(f"\n✓ Expected workflow:")
    print(f"  1. Navigate to base booking page")
    print(f"  2. Find available dates from calendar (li.slot-calendar__dates-item[data-available='true'])")
    print(f"  3. Click on target date link to navigate to date-specific page")
    print(f"  4. Extract slots using: button[data-day='{day}'][data-month='{month_abbr}']")
    
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
        
        driver = Driver(        
                    uc=False,        
                    headless2=False, 
                    no_sandbox=True,        
                    disable_gpu=True,        
                    headed=True,        
                )
        print(f"✓ Browser started")
        
        # Step 1: Navigate to base booking page (matching original working code)
        print(f"\n✓ Step 1: Navigating to base booking page...")
        print(f"  URL: {base_url}")
        driver.get(base_url)
        print(f"✓ Page loaded")
        
        # Wait for calendar to load (matching original working code approach)
        print(f"✓ Waiting for calendar to load...")
        try:
            # Wait for calendar dates to appear (they may load via JavaScript)
            driver.wait_for_element('li.slot-calendar__dates-item', timeout=15)
            print(f"✓ Calendar detected on page")
        except:
            # If wait fails, just sleep and continue (matching original code)
            print(f"⚠ Wait for calendar timed out, continuing anyway...")
            driver.sleep(5)
        
        # Additional wait to ensure calendar is fully loaded
        driver.sleep(3)
        
        # Step 2: Find available dates from calendar (matching original working code)
        print(f"\n" + "=" * 70)
        print("Step 2: Finding available dates from calendar...")
        print("=" * 70)
        
        # Try multiple times in case calendar is still loading
        dates = []
        date_elements = []  # For Selenium fallback
        
        for attempt in range(3):
            # Try with BeautifulSoup first (matching original code)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            dates = soup.find_all("li", {"class": "slot-calendar__dates-item", "data-available": "true"})
            
            # Also try with Selenium as fallback
            if len(dates) == 0:
                try:
                    date_elements = driver.find_elements("css selector", "li.slot-calendar__dates-item[data-available='true']")
                    if len(date_elements) > 0:
                        print(f"  Found {len(date_elements)} dates using Selenium (attempt {attempt + 1})")
                except:
                    pass
            
            if len(dates) > 0 or len(date_elements) > 0:
                break
            
            if attempt < 2:
                print(f"  Attempt {attempt + 1}: No dates found, waiting and retrying...")
                driver.sleep(2)
        
        # If Selenium found elements but BeautifulSoup didn't, convert them
        if len(dates) == 0 and len(date_elements) > 0:
            print(f"  Converting Selenium elements to BeautifulSoup objects...")
            for elem in date_elements:
                try:
                    html = elem.get_attribute('outerHTML')
                    date_item = BeautifulSoup(html, "html.parser").find("li")
                    if date_item:
                        dates.append(date_item)
                except:
                    pass
        
        print(f"✓ Found {len(dates)} available dates on calendar")
        
        # Also check for any calendar dates (even if not marked as available) for debugging
        if len(dates) == 0:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            all_calendar_dates = soup.find_all("li", {"class": "slot-calendar__dates-item"})
            print(f"  Debug: Found {len(all_calendar_dates)} total calendar date items (including unavailable)")
            
            # Also try with Selenium
            try:
                all_date_elems = driver.find_elements("css selector", "li.slot-calendar__dates-item")
                print(f"  Debug (Selenium): Found {len(all_date_elems)} total calendar date items")
            except:
                pass
            
            if len(all_calendar_dates) > 0:
                print(f"  Sample calendar dates found (first 5):")
                for i, date_item in enumerate(all_calendar_dates[:5], 1):
                    date_attr = date_item.get("data-date", "N/A")
                    available_attr = date_item.get("data-available", "N/A")
                    classes = date_item.get("class", [])
                    print(f"    {i}. data-date='{date_attr}', data-available='{available_attr}', class={classes}")
            
            print(f"\n⚠ No available dates found on calendar")
            print(f"  Saving page source to 'swingers_page_source.html' for inspection...")
            with open('swingers_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"  ✓ Page source saved")
            return False
        
        # Step 3: Find and click on target date link
        print(f"\n" + "=" * 70)
        print(f"Step 3: Looking for target date {date_str}...")
        print("=" * 70)
        
        target_date_found = False
        target_date_link = None
        
        for date_item in dates:
            date_item_str = date_item.get("data-date")
            if date_item_str == date_str:
                target_date_found = True
                # Find the link within this date item
                link_element = date_item.find("a")
                if link_element and link_element.get("href"):
                    target_date_link = "https://www.swingers.club" + link_element["href"]
                    print(f"✓ Found target date {date_str}")
                    print(f"  Link: {target_date_link}")
                    break
        
        if not target_date_found:
            print(f"⚠ Target date {date_str} not found in available dates")
            print(f"\n  Available dates found:")
            for date_item in dates[:10]:  # Show first 10
                print(f"    - {date_item.get('data-date', 'N/A')}")
            if len(dates) > 10:
                print(f"    ... and {len(dates) - 10} more")
            return False
        
        if not target_date_link:
            print(f"⚠ Could not find link for target date {date_str}")
            return False
        
        # Step 4: Navigate to target date page
        print(f"\n" + "=" * 70)
        print(f"Step 4: Navigating to target date page...")
        print("=" * 70)
        
        print(f"✓ Navigating to: {target_date_link}")
        driver.get(target_date_link)
        print(f"✓ Page loaded")
        
        # Wait for slots to load
        print(f"✓ Waiting for slots to load...")
        try:
            driver.wait_for_element('button[data-day][data-month]', timeout=15)
            print(f"✓ Slots detected on page")
        except:
            print(f"⚠ Wait for elements timed out, continuing anyway...")
            driver.sleep(5)
        
        # Additional wait to ensure all slots are loaded
        driver.sleep(3)
        
        # Step 5: Extract slots (matching original working code)
        print(f"\n" + "=" * 70)
        print("Step 5: Extracting slots from page...")
        print("=" * 70)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all("button", {"data-day": day, "data-month": month_abbr})
        
        print(f"✓ Found {len(slots)} slot buttons matching criteria")
        print(f"  (data-day='{day}', data-month='{month_abbr}')")
        
        # If no slots found, try without leading zero for day
        if len(slots) == 0 and day.startswith("0"):
            day_no_zero = str(int(day))
            print(f"  Trying alternative: data-day='{day_no_zero}' (without leading zero)")
            slots = soup.find_all("button", {"data-day": day_no_zero, "data-month": month_abbr})
            if len(slots) > 0:
                print(f"✓ Found {len(slots)} slots with data-day='{day_no_zero}'")
                day = day_no_zero
        
        if len(slots) == 0:
            print(f"\n⚠ No slots found with the expected selectors")
            print(f"\nDebugging information:")
            
            # Check for any slot buttons
            all_slot_buttons = soup.find_all("button", {"data-day": True, "data-month": True})
            print(f"  - Found {len(all_slot_buttons)} total slot buttons with data-day and data-month attributes")
            
            if len(all_slot_buttons) > 0:
                print(f"\n  Sample slot buttons found (first 5):")
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
        
        slots_count = len(slots)
        
        # Extract slot information (matching original working code)
        print(f"\n" + "=" * 70)
        print("Extracted Slots:")
        print("=" * 70)
        
        slots_data = []
        
        for slot in slots:
            # Status (matching original working code)
            status_el = slot.select_one("div.slot-search-result__low-stock")
            if status_el:
                status = status_el.get_text(strip=True)
            else:
                status = "Available"
            
            # Time (matching original working code)
            try:
                time_str = slot.find("span", {"class": "slot-search-result__time h5"}).get_text().strip()
            except:
                time_str = "None"
            
            # Price (matching original working code)
            try:
                price = slot.find("span", {"class": "slot-search-result__price-label"}).get_text().strip()
            except:
                price = "None"
            
            slots_data.append({
                'time': time_str,
                'price': price,
                'status': status
            })
            
            print(f"\n  Slot {len(slots_data)}:")
            print(f"    Time: {time_str}")
            print(f"    Price: {price}")
            print(f"    Status: {status}")
        
        print(f"\n" + "=" * 70)
        print("Test Results")
        print("=" * 70)
        print(f"✓ Successfully extracted {len(slots_data)} slots")
        print(f"✓ Date: {date_str}")
        print(f"✓ Guests: {guests}")
        print(f"✓ Base URL: {base_url}")
        if target_date_link:
            print(f"✓ Date page URL: {target_date_link}")
        
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

