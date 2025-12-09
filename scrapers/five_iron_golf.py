"""Five Iron Golf scraper for multiple NYC locations"""
from datetime import datetime
from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium.webdriver.common.keys import Keys
from time import sleep

# Global variables (will be set by the calling context)
scraping_status = {}
scraped_data = []


def create_driver_with_chrome_fallback():
    """Import and use the driver creation function from app.py"""
    # Import here to avoid circular imports
    import sys
    import importlib
    if 'app' in sys.modules:
        app_module = sys.modules['app']
        return app_module.create_driver_with_chrome_fallback()
    else:
        # Fallback: import app module
        from app import create_driver_with_chrome_fallback as create_driver
        return create_driver()


# Five Iron Golf location mappings
FIVE_IRON_LOCATIONS = {
    'fidi': 'NYC - FiDi',
    'flatiron': 'NYC - Flatiron',
    'grand_central': 'NYC - Grand Central',
    'herald_square': 'NYC - Herald Square',
    'long_island_city': 'NYC - Long Island City',
    'upper_east_side': 'NYC - Upper East Side',
    'rockefeller_center': 'NYC - Rockefeller Center'
}

# Venue name mappings for each location
FIVE_IRON_VENUE_NAMES = {
    'fidi': 'Five Iron Golf (NYC - FiDi)',
    'flatiron': 'Five Iron Golf (NYC - Flatiron)',
    'grand_central': 'Five Iron Golf (NYC - Grand Central)',
    'herald_square': 'Five Iron Golf (NYC - Herald Square)',
    'long_island_city': 'Five Iron Golf (NYC - Long Island City)',
    'upper_east_side': 'Five Iron Golf (NYC - Upper East Side)',
    'rockefeller_center': 'Five Iron Golf (NYC - Rockefeller Center)'
}


def scrape_five_iron_golf(guests, target_date, location='fidi'):
    """
    Five Iron Golf scraper function for a specific location
    
    Args:
        guests: Number of guests
        target_date: Target date in YYYY-MM-DD format
        location: Location identifier (fidi, flatiron, grand_central, etc.)
    
    Returns:
        Number of slots scraped
    """
    global scraping_status, scraped_data
    
    # Get location display name and venue name
    location_display = FIVE_IRON_LOCATIONS.get(location, 'NYC - FiDi')
    venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf (NYC - FiDi)')
    
    try:
        date_str = target_date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%m/%d/%Y")
        
        driver = create_driver_with_chrome_fallback()
        driver.set_page_load_timeout(20)

        try:
            driver.get("https://booking.fiveirongolf.com/session-length")
        except Exception:
            scraping_status["progress"] = "Page load timeout. Continuing..."
        
        scraping_status['progress'] = f'Navigating to Five Iron Golf {location_display}...'
        scraping_status['current_date'] = target_date
        
        try:
            driver.wait_for_element('div[role="combobox"][id="location-select"]', timeout=30)
        except Exception:
            scraping_status['progress'] = f'Page did not load properly for Five Iron Golf {location_display}'
            driver.quit()
            return 0
        
        # Select location
        driver.click('div[role="combobox"][id="location-select"]')
        driver.sleep(3)
        driver.js_click(f'//li[normalize-space()="{location_display}"]')
        
        scraping_status['progress'] = f'Setting date to {target_date}...'
        
        # Set date
        date_input = driver.find_element("css selector", 'input[placeholder="mm/dd/yyyy"]')
        date_input.send_keys(Keys.CONTROL, "a")
        date_input.send_keys(Keys.DELETE)
        driver.type('input[placeholder="mm/dd/yyyy"]', formatted_date)
        
        # Set party size
        scraping_status['progress'] = f'Setting party size to {guests}...'
        
        driver.click('div[role="combobox"][id="party_size_select"]')
        driver.js_click(f'//li[normalize-space()="{guests}"]')
        
        driver.sleep(7)
        
        scraping_status['progress'] = f'Searching for available slots on Five Iron Golf {location_display}...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('div.MuiToggleButtonGroup-root.css-9mqnp1')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Five Iron Golf {location_display}'
        
        if len(slots) == 0:
            scraping_status['progress'] = f'No slots available on Five Iron Golf {location_display}'
            driver.quit()
            return 0
        
        slots_count = 0
        for slot in slots:
            status = "Available"
            
            # Extract time
            try:
                time = slot.find_previous_sibling("h5").get_text(strip=True)
            except:
                time = "None"
            
            # Extract each duration + price separately
            buttons = slot.select("button.MuiToggleButton-root")
            
            for btn in buttons:
                try:
                    duration = btn.contents[0].strip()      # "2 hours"
                except:
                    duration = "None"
                
                price_el = btn.select_one("p")
                price = price_el.get_text(strip=True) if price_el else ""

                # Skip rows where price is missing
                if not price:
                    continue

                # Convert "2 hours" → "2h"
                dur_clean = duration.replace(" hours", "h").replace(" hour", "h").strip()

                # Final format: "2h : $58"
                desc = f"{dur_clean} : {price}"

                slot_data = {
                    'date': date_str,
                    'time': time,
                    'price': desc,
                    'status': status,
                    'timestamp': datetime.now().isoformat(),
                    'website': venue_name
                }

                scraped_data.append(slot_data)
                slots_count += 1
                scraping_status['total_slots_found'] = len(scraped_data)

        driver.quit()
        return slots_count
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e

