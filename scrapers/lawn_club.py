"""Lawn Club NYC scraper for multiple experience options using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

# Lawn Club option mappings
LAWN_CLUB_OPTIONS = {
    'indoor_gaming': 'Indoor Gaming Lawns',
    'curling_lawns': 'Curling Lawns & Cabins',
    'croquet_lawns': 'Croquet Lawns'
}

# Venue name mappings for each option
LAWN_CLUB_VENUE_NAMES = {
    'indoor_gaming': 'The Lawn Club (Indoor Gaming)',
    'curling_lawns': 'The Lawn Club (Curling Lawns)',
    'croquet_lawns': 'The Lawn Club (Croquet Lawns)'
}


# def scrape_lawn_club(guests, target_date, option='indoor_gaming', selected_time=None, selected_duration=None):
#     """
#     Lawn Club NYC scraper function for a specific option
    
#     Args:
#         guests: Number of guests
#         target_date: Target date in YYYY-MM-DD format
#         option: Option identifier (indoor_gaming, curling_lawns, croquet_lawns)
#         selected_time: Optional time selection
#         selected_duration: Optional duration selection
    
#     Returns:
#         List of slot dictionaries
#     """
#     results = []
    
#     # Get option display name and venue name
#     option_display = LAWN_CLUB_OPTIONS.get(option, 'Indoor Gaming Lawns')
#     venue_name = LAWN_CLUB_VENUE_NAMES.get(option, 'Lawn Club (Indoor Gaming)')
    
#     # Import helper functions from app (lazy import to avoid circular dependency)
#     try:
#         from app import (
#             LAWN_CLUB_TIME_OPTIONS,
#             LAWN_CLUB_DURATION_OPTIONS,
#             normalize_time_value,
#             normalize_duration_value,
#             adjust_picker
#         )
#     except ImportError:
#         import sys
#         if 'app' in sys.modules:
#             app_module = sys.modules['app']
#             LAWN_CLUB_TIME_OPTIONS = app_module.LAWN_CLUB_TIME_OPTIONS
#             LAWN_CLUB_DURATION_OPTIONS = app_module.LAWN_CLUB_DURATION_OPTIONS
#             normalize_time_value = app_module.normalize_time_value
#             normalize_duration_value = app_module.normalize_duration_value
#             adjust_picker = app_module.adjust_picker
#         else:
#             raise
    
#     try:
#         date_str = target_date
        
#         with BaseScraper() as scraper:
#             scraper.goto("https://www.sevenrooms.com/landing/lawnclubnyc", timeout=60000, wait_until="networkidle")
#             scraper.wait_for_timeout(8000)  # Wait for page to fully render
            
#             logger.info(f'Navigating to Lawn Club NYC {option_display}...')
            
#             # Wait for option link to be available
#             try:
#                 scraper.wait_for_selector(f'//a[contains(text(), "{option_display}")]', timeout=30000)
#             except Exception:
#                 logger.warning(f'Option link "{option_display}" not found')
#                 return results
            
#             scraper.click(f'//a[contains(text(), "{option_display}")]')
#             scraper.wait_for_timeout(5000)  # Wait for navigation
            
#             try:
#                 scraper.wait_for_selector('button[data-test="sr-calendar-date-button"]', timeout=60000)
#                 scraper.wait_for_timeout(3000)  # Additional wait for calendar to be ready
#             except Exception as e:
#                 logger.info('Page did not load properly for Lawn Club')
#                 return results
            
#             logger.info(f'Setting date to {target_date} and guests to {guests}...')
            
#             # Navigate to the correct date
#             dt = datetime.strptime(date_str, "%Y-%m-%d")
#             formatted = dt.strftime("%a, %b ") + str(dt.day)
            
#             while True:
#                 content = scraper.get_content()
#                 soup = BeautifulSoup(content, "html.parser")
#                 current_date_el = soup.find("button", {"data-test": "sr-calendar-date-button"})
#                 if not current_date_el:
#                     break
#                 current_date = current_date_el.find_all("div")[0].get_text()
#                 if str(formatted) == current_date:
#                     break
#                 try:
#                     scraper.click('button[aria-label="increment Date"]')
#                 except:
#                     break
            
#             # Set guest count - first decrement to minimum
#             while True:
#                 try:
#                     scraper.click('button[aria-label="decrement Guests"]')
#                 except:
#                     break
            
#             # Then increment to desired count
#             while True:
#                 content = scraper.get_content()
#                 soup = BeautifulSoup(content, "html.parser")
#                 guest_button = soup.find("button", {"data-test": "sr-guest-count-button"})
#                 if not guest_button:
#                     break
#                 current_guests = guest_button.find_all("div")[0].get_text().strip()
#                 if str(guests) == current_guests:
#                     break
                
#                 try:
#                     try:
#                         scraper.click('button[aria-label="increment Guests"]')
#                     except:
#                         scraper.click('button[aria-label="increment Guest"]')
#                 except:
#                     break
            
#             normalized_time = normalize_time_value(selected_time)
#             if normalized_time:
#                 logger.info(f'Selecting Lawn Club time {normalized_time}...')
#                 # Wait for time picker to be available
#                 try:
#                     scraper.wait_for_selector('button[data-test="sr-time-button"]', timeout=30000)
#                 except Exception:
#                     logger.warning("Time picker not found")
                
#                 if not adjust_picker(
#                     scraper.page,
#                     'button[data-test="sr-time-button"]',
#                     'button[aria-label="increment Time"]',
#                     'button[aria-label="decrement Time"]',
#                     LAWN_CLUB_TIME_OPTIONS,
#                     normalized_time,
#                     normalize_time_value
#                 ):
#                     logger.warning(f"Could not set Lawn Club time to {normalized_time}")
#                 scraper.wait_for_timeout(1000)  # Increased wait after time selection
            
#             normalized_duration = normalize_duration_value(selected_duration)
#             if normalized_duration:
#                 logger.info(f'Selecting Lawn Club duration {normalized_duration}...')
#                 # Wait for duration picker to be available
#                 try:
#                     scraper.wait_for_selector('button[data-test="sr-duration-picker"]', timeout=30000)
#                 except Exception:
#                     logger.warning("Duration picker not found")
                
#                 if not adjust_picker(
#                     scraper.page,
#                     'button[data-test="sr-duration-picker"]',
#                     'button[aria-label="increment duration"]',
#                     'button[aria-label="decrement duration"]',
#                     LAWN_CLUB_DURATION_OPTIONS,
#                     normalized_duration,
#                     normalize_duration_value
#                 ):
#                     logger.warning(f"Could not set Lawn Club duration to {normalized_duration}")
#                 scraper.wait_for_timeout(1000)  # Increased wait after duration selection
            
#             # Wait a moment to ensure URL has updated with all selections
#             scraper.wait_for_timeout(2000)  # Increased wait for URL update
            
#             # Capture the booking URL after all selections
#             booking_url = scraper.page.url
#             logger.info(f"[Lawn Club] Captured booking URL: {booking_url}")
            
#             # Search for availability
#             try:
#                 # Wait for search button to be available
#                 scraper.wait_for_selector('button[data-test="sr-search-button"]', timeout=30000)
#                 scraper.click('button[data-test="sr-search-button"]')
#                 scraper.wait_for_timeout(6000)  # Increased wait after clicking search
#             except Exception as e:
#                 logger.info('Could not click search button')
#                 return results
            
#             logger.info('Searching for available slots on Lawn Club...')
            
#             # Wait for results to load - wait for slots container
#             try:
#                 scraper.wait_for_selector('div.sc-huFNyZ, div[data-test="sr-time-slot-list"]', timeout=45000)
#             except Exception:
#                 logger.warning("Slots container not found, continuing anyway...")
            
#             scraper.wait_for_timeout(4000)  # Increased wait for results to fully render
            
#             content = scraper.get_content()
#             soup = BeautifulSoup(content, "html.parser")
            
#             # Try to find the slots container
#             slots_container = soup.find('div', {'class': 'sc-huFNyZ cINeur'})
#             if not slots_container:
#                 slots_container = soup.find('div', class_=lambda x: x and 'sc-huFNyZ' in x)
#                 if not slots_container:
#                     slots_container = soup.find('div', {'data-test': 'sr-time-slot-list'})
            
#             if not slots_container:
#                 logger.info('No slots available on Lawn Club or page structure changed')
#                 return results
            
#             slots = slots_container.find_all('button')
            
#             logger.info(f'Found {len(slots)} available slots on Lawn Club')
            
#             if len(slots) == 0:
#                 logger.info('No slots available on Lawn Club')
#                 return results
            
#             for slot in slots:
#                 status = "Available"
                
#                 try:
#                     time = slot.find_all("div")[0].get_text().strip()
#                 except:
#                     time = "None"
                
#                 try:
#                     desc = slot.find_all("div")[1].get_text().strip()
#                 except:
#                     desc = "None"
                
#                 slot_data = {
#                     'date': date_str,
#                     'time': time,
#                     'price': desc,
#                     'status': status,
#                     'timestamp': datetime.now().isoformat(),
#                     'website': venue_name,
#                     'booking_url': booking_url
#                 }
                
#                 results.append(slot_data)
        
#         return results
        
#     except Exception as e:
#         logger.error(f"Error scraping Lawn Club: {e}", exc_info=True)
#         raise e








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
        List of slot dictionaries
    """
    results = []
    
    # Get option display name and venue name
    option_display = LAWN_CLUB_OPTIONS.get(option, 'Indoor Gaming Lawns')
    venue_name = LAWN_CLUB_VENUE_NAMES.get(option, 'The Lawn Club (Indoor Gaming)')
    
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
        
        with BaseScraper() as scraper:
            print('start')
            scraper.goto("https://www.sevenrooms.com/landing/lawnclubnyc", timeout=60000, wait_until="networkidle")
            scraper.wait_for_timeout(8000)  # Wait for page to fully render
            
            logger.info(f'Navigating to Lawn Club NYC {option_display}...')
            
            # Wait for option link to be available
            try:
                scraper.wait_for_selector(f'//a[contains(text(), "{option_display}")]', timeout=30000)
            except Exception:
                logger.warning(f'Option link "{option_display}" not found')
                return results
            
            scraper.click(f'//a[contains(text(), "{option_display}")]')
            scraper.wait_for_timeout(5000)  # Wait for navigation
            
            try:
                scraper.wait_for_selector('button[data-test="sr-calendar-date-button"]', timeout=60000)
                scraper.wait_for_timeout(3000)  # Additional wait for calendar to be ready
            except Exception as e:
                logger.info('Page did not load properly for Lawn Club')
                return results
            
            logger.info(f'Setting date to {target_date} and guests to {guests}...')
            
            # Navigate to the correct date
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            formatted = dt.strftime("%a, %b ") + str(dt.day)
            
            while True:
                content = scraper.get_content()
                soup = BeautifulSoup(content, "html.parser")
                current_date_el = soup.find("button", {"data-test": "sr-calendar-date-button"})
                if not current_date_el:
                    break
                current_date = current_date_el.find_all("div")[0].get_text()
                if str(formatted) == current_date:
                    break
                try:
                    scraper.click('button[aria-label="increment Date"]')
                except:
                    break
            while True:
                content = scraper.get_content()
                soup = BeautifulSoup(content, "html.parser")
                guest_button = soup.find("button", {"data-test": "sr-guest-count-button"})
                if not guest_button:
                    break
                current_guests = guest_button.find_all("div")[0].get_text().strip()
                if str(guests) == current_guests:
                    break
                
                try:
                    try:
                        scraper.click('button[aria-label="increment Guests"]')
                    except:
                        scraper.click('button[aria-label="increment Guest"]')
                except:
                    break
            
            normalized_time = normalize_time_value(selected_time)
            if normalized_time:
                logger.info(f'Selecting Lawn Club time {normalized_time}...')
                # Wait for time picker to be available
                try:
                    scraper.wait_for_selector('button[data-test="sr-time-button"]', timeout=30000)
                except Exception:
                    logger.warning("Time picker not found")
                
                if not adjust_picker(
                    scraper.page,
                    'button[data-test="sr-time-button"]',
                    'button[aria-label="increment Time"]',
                    'button[aria-label="decrement Time"]',
                    LAWN_CLUB_TIME_OPTIONS,
                    normalized_time,
                    normalize_time_value
                ):
                    logger.warning(f"Could not set Lawn Club time to {normalized_time}")
                scraper.wait_for_timeout(1000)  # Increased wait after time selection
            
            normalized_duration = normalize_duration_value(selected_duration)
            if normalized_duration:
                logger.info(f'Selecting Lawn Club duration {normalized_duration}...')
                # Wait for duration picker to be available
                try:
                    scraper.wait_for_selector('button[data-test="sr-duration-picker"]', timeout=30000)
                except Exception:
                    logger.warning("Duration picker not found")
                
                if not adjust_picker(
                    scraper.page,
                    'button[data-test="sr-duration-picker"]',
                    'button[aria-label="increment duration"]',
                    'button[aria-label="decrement duration"]',
                    LAWN_CLUB_DURATION_OPTIONS,
                    normalized_duration,
                    normalize_duration_value
                ):
                    logger.warning(f"Could not set Lawn Club duration to {normalized_duration}")
                scraper.wait_for_timeout(1000)  # Increased wait after duration selection
            
            # Wait a moment to ensure URL has updated with all selections
            scraper.wait_for_timeout(2000)  # Increased wait for URL update
            
            # Capture the booking URL after all selections
            booking_url = scraper.page.url
            logger.info(f"[Lawn Club] Captured booking URL: {booking_url}")
            
            # Search for availability
            try:
                # Wait for search button to be available
                scraper.wait_for_selector('button[data-test="sr-search-button"]', timeout=30000)
                scraper.click('button[data-test="sr-search-button"]')
                scraper.wait_for_timeout(6000)  # Increased wait after clicking search
            except Exception as e:
                logger.info('Could not click search button')
                return results
            
            logger.info('Searching for available slots on Lawn Club...')
            
            # ---- WAIT FOR SEVENROOMS SLOT BUTTONS ----
            try:
                scraper.wait_for_selector('button[data-test="sr-timeslot-button"]', timeout=35000)
            except:
                logger.warning("⛔ No SevenRooms slot buttons found")
                return results

            scraper.wait_for_timeout(2000)

            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            # All slot buttons
            slot_buttons = soup.select('button[data-test="sr-timeslot-button"]')

            if not slot_buttons:
                logger.info("⚠ WARNING: No slots found (structure changed or no availability)")
                return results

            logger.info(f"Found {len(slot_buttons)} Lawn Club slots")

            for btn in slot_buttons:
                try:
                    time_text = btn.find_all("div")[0].get_text(strip=True)
                except:
                    time_text = "None"

                try:
                    desc_text = btn.find_all("div")[1].get_text(strip=True)
                except:
                    desc_text = "None"

                slot_data = {
                    "date": date_str,
                    "time": time_text,
                    "price": desc_text,
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": venue_name,
                    "booking_url": booking_url
                }

                results.append(slot_data)
        
        return results
        
    except Exception as e:
        logger.error(f"Error scraping Lawn Club: {e}", exc_info=True)
        raise e
