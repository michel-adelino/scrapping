"""Five Iron Golf scraper for multiple NYC locations using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from playwright.sync_api import Page
import logging

logger = logging.getLogger(__name__)

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


# def scrape_five_iron_golf(guests, target_date, location='fidi'):
#     """
#     Five Iron Golf scraper function for a specific location
    
#     Args:
#         guests: Number of guests
#         target_date: Target date in YYYY-MM-DD format
#         location: Location identifier (fidi, flatiron, grand_central, etc.)
    
#     Returns:
#         List of slot dictionaries
#     """
#     results = []
    
#     # Get location display name and venue name
#     location_display = FIVE_IRON_LOCATIONS.get(location, 'NYC - FiDi')
#     venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf (NYC - FiDi)')
    
#     try:
#         date_str = target_date
#         dt = datetime.strptime(date_str, "%Y-%m-%d")
#         formatted_date = dt.strftime("%m/%d/%Y")
        
#         with BaseScraper() as scraper:
#             scraper.page.set_default_timeout(60000)
            
#             try:
#                 scraper.goto("https://booking.fiveirongolf.com/session-length", timeout=60000, wait_until="networkidle")
#                 scraper.wait_for_timeout(8000)  # Wait for page to fully render
#             except Exception:
#                 logger.info("Page load timeout. Continuing...")
            
#             logger.info(f'Navigating to Five Iron Golf {location_display}...')
            
#             try:
#                 scraper.wait_for_selector('div[role="combobox"][id="location-select"]', timeout=60000)
#                 scraper.wait_for_timeout(3000)  # Additional wait for dropdown to be ready
#             except Exception:
#                 logger.info(f'Page did not load properly for Five Iron Golf {location_display}')
#                 return results
            
#             # Select location
#             scraper.click('div[role="combobox"][id="location-select"]')
#             scraper.wait_for_timeout(4000)  # Increased wait for dropdown to open
            
#             # Wait for location option to be available
#             try:
#                 scraper.wait_for_selector(f'//li[normalize-space()="{location_display}"]', timeout=30000)
#             except Exception:
#                 logger.warning(f"Location option '{location_display}' not found")
            
#             scraper.click(f'//li[normalize-space()="{location_display}"]')
#             scraper.wait_for_timeout(3000)  # Wait for location selection to apply
            
#             logger.info(f'Setting date to {target_date}...')
            
#             # Set date - wait for date input to be available
#             try:
#                 scraper.wait_for_selector('input[placeholder="mm/dd/yyyy"]', timeout=30000)
#             except Exception:
#                 logger.warning("Date input not found")
            
#             date_input = scraper.locator('input[placeholder="mm/dd/yyyy"]')
#             date_input.click()
#             scraper.wait_for_timeout(500)
#             date_input.fill('')  # Clear
#             scraper.wait_for_timeout(500)
#             date_input.fill(formatted_date)
#             scraper.wait_for_timeout(2000)  # Wait for date to be set
            
#             # Set party size
#             logger.info(f'Setting party size to {guests}...')
            
#             try:
#                 scraper.wait_for_selector('div[role="combobox"][id="party_size_select"]', timeout=30000)
#             except Exception:
#                 logger.warning("Party size selector not found")
            
#             scraper.click('div[role="combobox"][id="party_size_select"]')
#             scraper.wait_for_timeout(3000)  # Wait for dropdown to open
            
#             # Wait for party size option to be available
#             try:
#                 scraper.wait_for_selector(f'//li[normalize-space()="{guests}"]', timeout=30000)
#             except Exception:
#                 logger.warning(f"Party size option '{guests}' not found")
            
#             scraper.click(f'//li[normalize-space()="{guests}"]')
#             scraper.wait_for_timeout(5000)  # Wait for party size selection to apply
            
#             # Wait for slots to load after all selections
#             logger.info(f'Searching for available slots on Five Iron Golf {location_display}...')
            
#             try:
#                 scraper.wait_for_selector('div.MuiToggleButtonGroup-root', timeout=45000)
#             except Exception:
#                 logger.warning("Slot container not found, continuing anyway...")
            
#             scraper.wait_for_timeout(5000)  # Increased wait for slots to fully render
            
#             content = scraper.get_content()
#             soup = BeautifulSoup(content, "html.parser")
#             slots = soup.select('div.MuiToggleButtonGroup-root.css-9mqnp1')
            
#             logger.info(f'Found {len(slots)} available slots on Five Iron Golf {location_display}')
            
#             if len(slots) == 0:
#                 logger.info(f'No slots available on Five Iron Golf {location_display}')
#                 return results
            
#             for slot in slots:
#                 status = "Available"
                
#                 # Extract time
#                 try:
#                     time = slot.find_previous_sibling("h5").get_text(strip=True)
#                 except:
#                     time = "None"
                
#                 # Extract each duration + price separately
#                 buttons = slot.select("button.MuiToggleButton-root")
                
#                 for btn in buttons:
#                     try:
#                         duration = btn.contents[0].strip()  # "2 hours"
#                     except:
#                         duration = "None"
                    
#                     price_el = btn.select_one("p")
#                     price = price_el.get_text(strip=True) if price_el else ""

#                     # Skip rows where price is missing
#                     if not price:
#                         continue

#                     # Convert "2 hours" → "2h"
#                     dur_clean = duration.replace(" hours", "h").replace(" hour", "h").strip()

#                     # Final format: "2h : $58"
#                     desc = f"{dur_clean} : {price}"

#                     slot_data = {
#                         'date': date_str,
#                         'time': time,
#                         'price': desc,
#                         'status': status,
#                         'timestamp': datetime.now().isoformat(),
#                         'website': venue_name
#                     }

#                     results.append(slot_data)
        
#         return results
        
#     except Exception as e:
#         logger.error(f"Error scraping Five Iron Golf: {e}", exc_info=True)
#         raise e





def scrape_five_iron_golf(guests, target_date, location='fidi'):
    """
    Five Iron Golf scraper function for a specific location
    
    Args:
        guests: Number of guests
        target_date: Target date in YYYY-MM-DD format
        location: Location identifier (fidi, flatiron, grand_central, etc.)
    
    Returns:
        List of slot dictionaries
    """
    results = []
    
    # Get location display name and venue name
    location_display = FIVE_IRON_LOCATIONS.get(location, 'NYC - FiDi')
    venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf (NYC - FiDi)')
    
    try:
        date_str = target_date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%m/%d/%Y")
        
        with BaseScraper() as scraper:
            scraper.page.set_default_timeout(60000)

            # ⚡ Try loading but stop early
            try:
                scraper.goto(
                    "https://booking.fiveirongolf.com/session-length",
                    timeout=5000,                   # very small timeout
                    wait_until="domcontentloaded"   # do NOT wait for networkidle
                )
            except Exception:
                logger.info("Page load timeout. Continuing...")
                
            # scraper.page.evaluate("window.stop()")
            logger.info(f'Navigating to Five Iron Golf {location_display}...')
            
            try:
                # Wait for dropdown to appear (full 60 seconds)
                scraper.page.locator('div[role="combobox"][id="location-select"]').wait_for(
                    timeout=60000,
                    state="visible"
                )
                print("[DEBUG] Location dropdown is visible")
                scraper.wait_for_timeout(2000)  # small safety delay
            except Exception as e:
                print("[ERROR] Dropdown load failure:", e)
                logger.info(f'Page did not load properly for Five Iron Golf {location_display}')
                return results
            
            # Select location - improved for headless Ubuntu
            scraper.click('div[role="combobox"][id="location-select"]')
            scraper.wait_for_timeout(2000)  # Wait for dropdown to start opening
            
            # Wait for dropdown menu to be visible (ul element)
            try:
                scraper.wait_for_selector('ul[role="listbox"]', timeout=10000)
                scraper.wait_for_timeout(1000)  # Additional wait for items to render
            except Exception as e:
                logger.warning(f"Dropdown menu not found: {e}")
            
            # Wait for location option to be available and visible
            location_selector = f'//li[normalize-space()="{location_display}"]'
            try:
                # Wait for element to be attached and visible
                scraper.page.wait_for_selector(location_selector, timeout=30000, state="visible")
                scraper.wait_for_timeout(500)  # Small delay to ensure it's clickable
            except Exception as e:
                logger.warning(f"Location option '{location_display}' not found or not visible: {e}")
                # Try to find all available locations for debugging
                try:
                    all_locations = scraper.page.query_selector_all('ul[role="listbox"] li')
                    available = [li.inner_text() for li in all_locations[:5]]  # First 5 for debugging
                    logger.warning(f"Available location options (first 5): {available}")
                except:
                    pass
                raise
            
            # Scroll element into view before clicking (important for headless)
            try:
                element = scraper.page.locator(location_selector)
                element.scroll_into_view_if_needed()
                scraper.wait_for_timeout(300)
            except Exception as e:
                logger.debug(f"Could not scroll element into view: {e}")
            
            # Click the location option - try regular click first, fallback to JS click
            try:
                scraper.click(location_selector)
            except Exception as click_error:
                logger.warning(f"Regular click failed, trying JavaScript click: {click_error}")
                # Fallback: Use JavaScript click (more reliable in headless mode)
                try:
                    scraper.page.evaluate(f"""
                        () => {{
                            const items = Array.from(document.querySelectorAll('ul[role="listbox"] li'));
                            const target = items.find(li => li.textContent.trim() === '{location_display}');
                            if (target) {{
                                target.click();
                                return true;
                            }}
                            return false;
                        }}
                    """)
                    logger.info("Location selected using JavaScript click")
                except Exception as js_error:
                    logger.error(f"JavaScript click also failed: {js_error}")
                    raise click_error  # Raise original error
            
            scraper.wait_for_timeout(3000)  # Wait for location selection to apply
            
            logger.info(f'Setting date to {target_date}...')
            
            # Set date - wait for date input to be available
            try:
                scraper.wait_for_selector('input[placeholder="mm/dd/yyyy"]', timeout=30000)
            except Exception:
                logger.warning("Date input not found")
            
            date_input = scraper.locator('input[placeholder="mm/dd/yyyy"]')
            date_input.click()
            scraper.wait_for_timeout(500)
            date_input.fill('')  # Clear
            scraper.wait_for_timeout(500)
            date_input.fill(formatted_date)
            scraper.wait_for_timeout(2000)  # Wait for date to be set
            
            # Set party size
            logger.info(f'Setting party size to {guests}...')
            
            try:
                scraper.wait_for_selector('div[role="combobox"][id="party_size_select"]', timeout=30000)
            except Exception:
                logger.warning("Party size selector not found")
            
            scraper.click('div[role="combobox"][id="party_size_select"]')
            scraper.wait_for_timeout(3000)  # Wait for dropdown to open
            
            # Wait for party size option to be available
            try:
                scraper.wait_for_selector(f'//li[normalize-space()="{guests}"]', timeout=30000)
            except Exception:
                logger.warning(f"Party size option '{guests}' not found")
            
            scraper.click(f'//li[normalize-space()="{guests}"]')
            scraper.wait_for_timeout(5000)  # Wait for party size selection to apply
            
            # Wait for slots to load after all selections
            logger.info(f'Searching for available slots on Five Iron Golf {location_display}...')
            
            try:
                scraper.wait_for_selector('div.MuiToggleButtonGroup-root', timeout=45000)
            except Exception:
                logger.warning("Slot container not found, continuing anyway...")
            
            scraper.wait_for_timeout(5000)  # Increased wait for slots to fully render
            
            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")
            slots = soup.select('div.MuiToggleButtonGroup-root.css-9mqnp1')
            
            logger.info(f'Found {len(slots)} available slots on Five Iron Golf {location_display}')
            
            if len(slots) == 0:
                logger.info(f'No slots available on Five Iron Golf {location_display}')
                return results
            
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
                        duration = btn.contents[0].strip()  # "2 hours"
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

                    results.append(slot_data)
        
        return results
        
    except Exception as e:
        logger.error(f"Error scraping Five Iron Golf: {e}", exc_info=True)
        raise e
