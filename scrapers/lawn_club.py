"""Lawn Club NYC scraper for multiple experience options"""
from datetime import datetime
from bs4 import BeautifulSoup
from seleniumbase import Driver
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


# Lawn Club option mappings
LAWN_CLUB_OPTIONS = {
    'indoor_gaming': 'Indoor Gaming Lawns',
    'curling_lawns': 'Curling Lawns & Cabins',
    'croquet_lawns': 'Croquet Lawns'
}

# Venue name mappings for each option
LAWN_CLUB_VENUE_NAMES = {
    'indoor_gaming': 'Lawn Club (Indoor Gaming)',
    'curling_lawns': 'Lawn Club (Curling Lawns)',
    'croquet_lawns': 'Lawn Club (Croquet Lawns)'
}


def scrape_lawn_club(guests, target_date, option='indoor_gaming', selected_time=None, selected_duration=None):
    """
    Lawn Club NYC scraper function for a specific option
    
    Args:
        guests: Number of guests
        target_date: Target date in YYYY-MM-DD format
        option: Option identifier (indoor_gaming, curling_lawns, croquet_lawns)
        selected_time: Optional time selection
        selected_duration: Optional duration selection
    
    Returns:
        Number of slots scraped
    """
    global scraping_status, scraped_data
    
    # Get option display name and venue name
    option_display = LAWN_CLUB_OPTIONS.get(option, 'Indoor Gaming Lawns')
    venue_name = LAWN_CLUB_VENUE_NAMES.get(option, 'Lawn Club (Indoor Gaming)')
    
    # Import helper functions from app (lazy import to avoid circular dependency)
    try:
        from app import (
            LAWN_CLUB_TIME_OPTIONS,
            LAWN_CLUB_DURATION_OPTIONS,
            normalize_time_value,
            normalize_duration_value,
            adjust_picker
        )
    except ImportError:
        # Fallback: import directly
        import sys
        if 'app' in sys.modules:
            app_module = sys.modules['app']
            LAWN_CLUB_TIME_OPTIONS = app_module.LAWN_CLUB_TIME_OPTIONS
            LAWN_CLUB_DURATION_OPTIONS = app_module.LAWN_CLUB_DURATION_OPTIONS
            normalize_time_value = app_module.normalize_time_value
            normalize_duration_value = app_module.normalize_duration_value
            adjust_picker = app_module.adjust_picker
        else:
            raise
    
    try:
        date_str = target_date
        # Use retry-enabled driver creation to handle Chrome crashes
        driver = create_driver_with_chrome_fallback()
        driver.get("https://www.sevenrooms.com/landing/lawnclubnyc")
        
        scraping_status['progress'] = f'Navigating to Lawn Club NYC {option_display}...'
        
        driver.click(f'//a[contains(text(), "{option_display}")]')
        
        try:
            driver.wait_for_element('button[data-test="sr-calendar-date-button"]', timeout=30)
        except Exception as e:
            scraping_status['progress'] = 'Page did not load properly for Lawn Club'
            driver.quit()
            return 0
        
        scraping_status['progress'] = f'Setting date to {target_date} and guests to {guests}...'
        scraping_status['current_date'] = target_date
        
        # Navigate to the correct date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted = dt.strftime("%a, %b ") + str(dt.day)
        
        while True:
            temp = BeautifulSoup(driver.page_source, "html.parser")
            current_date_el = temp.find("button", {"data-test": "sr-calendar-date-button"})
            if not current_date_el:
                break
            current_date = current_date_el.find_all("div")[0].get_text()
            print(f"Current date: {current_date}, Target: {formatted}")
            if str(formatted) == current_date:
                break
            try:
                driver.click('button[aria-label="increment Date"]')
            except:
                break
        
        # Set guest count - first decrement to minimum
        while True:
            try:
                driver.click('button[aria-label="decrement Guests"]')
            except:
                break
        
        # Then increment to desired count
        while True:
            temp = BeautifulSoup(driver.page_source, "html.parser")
            guest_button = temp.find("button", {"data-test": "sr-guest-count-button"})
            if not guest_button:
                break
            current_guests = guest_button.find_all("div")[0].get_text().strip()
            if str(guests) == current_guests:
                break
            
            try:
                try:
                    driver.click('button[aria-label="increment Guests"]')
                except:
                    driver.click('button[aria-label="increment Guest"]')
            except:
                break
        
        normalized_time = normalize_time_value(selected_time)
        if normalized_time:
            scraping_status['progress'] = f'Selecting Lawn Club time {normalized_time}...'
            if not adjust_picker(
                driver,
                'button[data-test="sr-time-button"]',
                'button[aria-label="increment Time"]',
                'button[aria-label="decrement Time"]',
                LAWN_CLUB_TIME_OPTIONS,
                normalized_time,
                normalize_time_value
            ):
                raise RuntimeError(f"Could not set Lawn Club time to {normalized_time}")
            driver.sleep(0.3)
        
        normalized_duration = normalize_duration_value(selected_duration)
        if normalized_duration:
            scraping_status['progress'] = f'Selecting Lawn Club duration {normalized_duration}...'
            if not adjust_picker(
                driver,
                'button[data-test="sr-duration-picker"]',
                'button[aria-label="increment duration"]',
                'button[aria-label="decrement duration"]',
                LAWN_CLUB_DURATION_OPTIONS,
                normalized_duration,
                normalize_duration_value
            ):
                raise RuntimeError(f"Could not set Lawn Club duration to {normalized_duration}")
            driver.sleep(0.3)
        
        # Wait a moment to ensure URL has updated with all selections
        driver.sleep(0.5)
        
        # Capture the booking URL after all selections (date, guests, time, duration)
        booking_url = driver.current_url
        print(f"[Lawn Club] Captured booking URL: {booking_url}")
        
        # Search for availability
        try:
            driver.click('button[data-test="sr-search-button"]')
            driver.sleep(4)
        except Exception as e:
            scraping_status['progress'] = 'Could not click search button'
            driver.quit()
            return 0
        
        scraping_status['progress'] = 'Searching for available slots on Lawn Club...'
        
        # Wait a bit more for results to load
        driver.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Try to find the slots container - handle case where it might not exist
        slots_container = soup.find('div', {'class': 'sc-huFNyZ cINeur'})
        if not slots_container:
            # Try alternative selectors
            slots_container = soup.find('div', class_=lambda x: x and 'sc-huFNyZ' in x)
            if not slots_container:
                # Try finding any container with time slots
                slots_container = soup.find('div', {'data-test': 'sr-time-slot-list'})
        
        if not slots_container:
            scraping_status['progress'] = 'No slots available on Lawn Club or page structure changed'
            driver.quit()
            return 0
        
        slots = slots_container.find_all('button')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Lawn Club'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Lawn Club'
            driver.quit()
            return 0
        
        slots_count = 0
        for slot in slots:
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find_all("div")[0].get_text().strip()
            except:
                time = "None"
                
            # Description (using as price equivalent)
            try:
                desc = slot.find_all("div")[1].get_text().strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': date_str,
                'time': time,
                'price': desc,  # Using description as price for consistency
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': venue_name,
                'booking_url': booking_url  # URL to the date/guest selection page for this option
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

