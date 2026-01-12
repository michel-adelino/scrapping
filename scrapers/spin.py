"""SPIN NYC scraper using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

# Venue name mappings for each location
SPIN_VENUE_NAMES = {
    'flatiron': 'SPIN (NYC - Flatiron)',
    'midtown': 'SPIN (NYC - Midtown)'
}

# URL mappings for each location
SPIN_URLS = {
    'flatiron': 'https://wearespin.com/location/new-york-flatiron/table-reservations/',
    'midtown': 'https://wearespin.com/location/new-york-midtown/table-reservations/'
}


def scrape_spin(guests, target_date, selected_time=None, location='flatiron'):
    """SPIN NYC scraper function (Playwright version)"""

    results = []

    # Import helper functions dynamically (with error handling for test environments)
    import sys
    LAWN_CLUB_TIME_OPTIONS = []
    normalize_time_value = None
    adjust_picker = None
    
    # Try to get functions from already loaded module first (avoids triggering db init)
    if 'app' in sys.modules:
        try:
            app_module = sys.modules['app']
            LAWN_CLUB_TIME_OPTIONS = getattr(app_module, 'LAWN_CLUB_TIME_OPTIONS', [])
            normalize_time_value = getattr(app_module, 'normalize_time_value', None)
            adjust_picker = getattr(app_module, 'adjust_picker', None)
        except Exception as e:
            logger.warning(f"Could not get functions from loaded app module: {e}")
    
    # If not available from loaded module, try importing
    if not normalize_time_value or not adjust_picker:
        try:
            from app import (
                LAWN_CLUB_TIME_OPTIONS,
                normalize_time_value,
                adjust_picker,
            )
        except Exception as e:
            logger.warning(f"Could not import from app: {e}. Using fallback functions.")
            # Fallback: define minimal versions for testing
            if not LAWN_CLUB_TIME_OPTIONS:
                LAWN_CLUB_TIME_OPTIONS = []
            if not normalize_time_value:
                def normalize_time_value(raw_value):
                    if not raw_value:
                        return None
                    return raw_value.strip().upper()
            if not adjust_picker:
                def adjust_picker(*args, **kwargs):
                    logger.warning("adjust_picker not available, skipping time adjustment")
                    return False

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%a, %b ") + str(dt.day)

        with BaseScraper() as scraper:

            # ---- LOAD ROOT PAGE ----
            # Get URL for the specified location
            base_url = SPIN_URLS.get(location, SPIN_URLS['flatiron'])
            
            # Try multiple load strategies for headless compatibility
            page_loaded = False
            for wait_strategy in ["networkidle", "load", "domcontentloaded"]:
                try:
                    scraper.goto(
                        base_url,
                        timeout=30000,
                        wait_until=wait_strategy
                    )
                    logger.info(f"SPIN page loaded with {wait_strategy}: {base_url}")
                    page_loaded = True
                    break
                except Exception as e:
                    logger.debug(f"SPIN page load with {wait_strategy} failed: {e}")
                    continue
            
            if not page_loaded:
                logger.warning("SPIN page load failed with all strategies, continuing anyway")
                try:
                    scraper.goto(base_url, timeout=30000, wait_until="commit")
                except:
                    pass

            # Wait for page to be fully interactive (longer wait for headless)
            scraper.wait_for_timeout(3000)
            
            # Wait for JavaScript to execute
            try:
                scraper.page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

            # ---- CLOSE POPUPS ----
            try:
                scraper.page.evaluate("""
                    document.querySelectorAll('.elementor-popup-modal').forEach(modal => {
                        let btn = modal.querySelector('.elementor-popup-modal-close, button[aria-label="Close"]');
                        if(btn) btn.click();
                        modal.style.display = "none";
                    });
                """)
            except:
                pass

            scraper.wait_for_timeout(2000)
            
            # Try to trigger elementor off-canvas widget via JavaScript
            # Wait for elementor to be ready (important for headless)
            try:
                scraper.page.wait_for_function(
                    "window.elementorFrontend !== undefined",
                    timeout=10000
                )
                logger.info("SPIN elementorFrontend is ready")
            except:
                logger.warning("SPIN elementorFrontend not detected, continuing anyway")
            
            try:
                result = scraper.page.evaluate("""
                    () => {
                        let triggered = false;
                        // Try to trigger elementor off-canvas widget
                        if (window.elementorFrontend && window.elementorFrontend.hooks) {
                            try {
                                const settings = {id: 'c88e5ca', displayMode: 'open'};
                                window.elementorFrontend.hooks.doAction('off_canvas:open', settings);
                                triggered = true;
                            } catch(e) {
                                console.log('Elementor hook failed:', e);
                            }
                        }
                        // Also try clicking elementor action links
                        const actionLinks = document.querySelectorAll('a[href*="elementor-action"]');
                        actionLinks.forEach(link => {
                            if (link.href.includes('off_canvas')) {
                                link.click();
                                triggered = true;
                            }
                        });
                        return triggered;
                    }
                """)
                if result:
                    logger.info("SPIN triggered elementor off-canvas via JavaScript")
                scraper.wait_for_timeout(3000)  # Longer wait for headless
            except Exception as e:
                logger.warning(f"SPIN JavaScript trigger failed: {e}")

            # ---- CLICK RESERVE BUTTON ----
            # Try multiple approaches to open the reservation widget
            button_clicked = False
            
            # First, try JavaScript to find and click the button (more reliable in headless)
            try:
                clicked = scraper.page.evaluate("""
                    () => {
                        // Wait a bit for elements to be ready
                        let btn = null;
                        
                        // Try specific elementor element
                        btn = document.querySelector('div.elementor-element.elementor-element-16e99e3.elementor-widget-button a, div.elementor-element.elementor-element-16e99e3.elementor-widget-button button');
                        if (btn && btn.offsetParent !== null) {  // Check if visible
                            btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => btn.click(), 100);
                            return true;
                        }
                        
                        // Try any elementor button with reservation link
                        btn = document.querySelector('div.elementor-widget-button a[href*="table-reservations"], div.elementor-widget-button a[href*="#elementor-action"]');
                        if (btn && btn.offsetParent !== null) {
                            btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => btn.click(), 100);
                            return true;
                        }
                        
                        // Try finding by text (more lenient for headless)
                        const allLinks = document.querySelectorAll('a, button');
                        for (let el of allLinks) {
                            if (el.offsetParent === null) continue;  // Skip hidden elements
                            const text = (el.textContent || el.innerText || '').trim().toLowerCase();
                            if ((text.includes('reserve') || text.includes('book') || text.includes('table')) && 
                                (el.href && (el.href.includes('table-reservations') || el.href.includes('elementor-action')))) {
                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => el.click(), 100);
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                if clicked:
                    button_clicked = True
                    logger.info("SPIN reservation button clicked via JavaScript")
                    scraper.wait_for_timeout(3000)  # Longer wait for headless
            except Exception as e:
                logger.warning(f"SPIN JavaScript button click failed: {e}")
            
            # If JavaScript didn't work, try Playwright selectors
            if not button_clicked:
                button_selectors = [
                    'div.elementor-element.elementor-element-16e99e3.elementor-widget-button a',
                    'div.elementor-element.elementor-element-16e99e3.elementor-widget-button button',
                    'div.elementor-widget-button a[href*="table-reservations"]',
                    'div.elementor-widget-button a[href*="#elementor-action"]',
                    'a[href*="table-reservations"]',
                ]
                
                for selector in button_selectors:
                    try:
                        scraper.page.wait_for_selector(selector, timeout=5000, state='visible')
                        scraper.click(selector)
                        button_clicked = True
                        logger.info(f"SPIN reservation button clicked using selector: {selector}")
                        scraper.wait_for_timeout(2000)
                        break
                    except:
                        continue
                
                # Try text-based matching with Playwright
                if not button_clicked:
                    text_selectors = [
                        ('a', 'Reserve'),
                        ('button', 'Reserve'),
                        ('a', 'Book'),
                        ('button', 'Book'),
                    ]
                    
                    for tag, text in text_selectors:
                        try:
                            element = scraper.page.locator(f'{tag}:has-text("{text}")').first
                            if element.is_visible(timeout=5000):
                                element.click()
                                button_clicked = True
                                logger.info(f"SPIN reservation button clicked using text: {text}")
                                scraper.wait_for_timeout(2000)
                                break
                        except:
                            continue
            
            if not button_clicked:
                logger.warning("SPIN reservation button not found with any selector")
                # Log available buttons for debugging
                try:
                    available_buttons = scraper.page.evaluate("""
                        () => {
                            const buttons = [];
                            document.querySelectorAll('a, button').forEach(el => {
                                const text = (el.textContent || el.innerText || '').trim();
                                if (text && (text.toLowerCase().includes('reserve') || text.toLowerCase().includes('book') || text.toLowerCase().includes('table'))) {
                                    buttons.push({
                                        tag: el.tagName,
                                        text: text.substring(0, 50),
                                        href: el.href || '',
                                        classes: el.className || ''
                                    });
                                }
                            });
                            return buttons;
                        }
                    """)
                    logger.info(f"SPIN available reservation-related elements: {available_buttons}")
                except:
                    pass
                
                # Fallback: Try navigating with hash fragment to trigger off-canvas
                logger.info("SPIN trying fallback: navigating with hash fragment")
                try:
                    hash_url = base_url + "#elementor-action%3Aaction%3Doff_canvas%3Aopen%26settings%3DeyJpZCI6ImM4OGU1Y2EiLCJkaXNwbGF5TW9kZSI6Im9wZW4ifQ%3D%3D"
                    scraper.goto(hash_url, timeout=30000, wait_until="networkidle")
                    scraper.wait_for_timeout(3000)
                    logger.info("SPIN navigated with hash fragment, checking for iframe...")
                except Exception as e:
                    logger.warning(f"SPIN hash fragment navigation failed: {e}")
                
                # Check if iframe appeared after hash navigation
                try:
                    iframe_check = scraper.page.query_selector('iframe[src*="sevenrooms"], iframe[nitro-lazy-src*="sevenrooms"]')
                    if iframe_check:
                        logger.info("SPIN iframe found after hash navigation")
                        button_clicked = True  # Consider it successful if iframe is present
                except:
                    pass
                
                if not button_clicked:
                    return results

            # Wait longer for the widget to open (VPS/headless might be slower)
            scraper.wait_for_timeout(5000)
            
            # Additional wait for iframe to start loading
            try:
                scraper.page.wait_for_function(
                    "document.querySelector('iframe[src*=\"sevenrooms\"], iframe[nitro-lazy-src*=\"sevenrooms\"]') !== null",
                    timeout=10000
                )
                logger.info("SPIN detected iframe element in DOM")
            except:
                logger.debug("SPIN iframe not yet in DOM, continuing anyway")

            # ---- GET SevenRooms Iframe ----
            # Wait for iframe to load with multiple possible selectors
            iframe_handle = None
            iframe_selectors = [
                'iframe[nitro-lazy-src*="sevenrooms.com/reservations/spinyc"]',
                'iframe[src*="sevenrooms.com/reservations/spinyc"]',
                'iframe[nitro-lazy-src*="sevenrooms.com"]',
                'iframe[src*="sevenrooms.com"]',
                'iframe[nitro-lazy-src*="sevenrooms"]',
                'iframe[src*="sevenrooms"]',
            ]
            
            logger.info("SPIN waiting for SevenRooms iframe to load...")
            for selector in iframe_selectors:
                try:
                    # In headless, try 'attached' first (element exists), then check if it has content
                    scraper.page.wait_for_selector(selector, timeout=15000, state='attached')
                    iframe_handle = scraper.page.query_selector(selector)
                    if iframe_handle:
                        logger.info(f"SPIN SevenRooms iframe found using selector: {selector}")
                        # Wait for iframe to have a src or be ready (important for headless)
                        try:
                            scraper.page.wait_for_function(
                                f"document.querySelector('{selector}') && (document.querySelector('{selector}').src || document.querySelector('{selector}').getAttribute('nitro-lazy-src'))",
                                timeout=5000
                            )
                        except:
                            pass
                        # Wait a bit more for iframe to be ready
                        scraper.wait_for_timeout(3000)  # Longer wait for headless
                        break
                except Exception as e:
                    logger.debug(f"SPIN iframe selector {selector} failed: {e}")
                    continue
            
            if not iframe_handle:
                logger.warning("SPIN SevenRooms iframe not found with any selector")
                return results

            try:
                frame = iframe_handle.content_frame()
                if not frame:
                    logger.warning("SPIN iframe content frame is None")
                    return results
                # Wait for iframe to be ready
                scraper.wait_for_timeout(1000)
            except Exception as e:
                logger.error(f"Could not load iframe: {e}")
                return results

            # ---- DATE PICKER ----
            try:
                frame.wait_for_selector('button[data-test="sr-calendar-date-button"]', timeout=15000)
                logger.info("SPIN date button found")
            except Exception as e:
                logger.warning(f"SPIN date button not found: {e}")
                return results

            # increment date until matches
            max_date_attempts = 50  # Prevent infinite loop
            date_attempts = 0
            while date_attempts < max_date_attempts:
                try:
                    cur = frame.eval_on_selector(
                        'button[data-test="sr-calendar-date-button"] div:nth-child(1)',
                        'el => el.textContent.trim()'
                    )
                    if cur == formatted_date:
                        logger.info(f"SPIN date matched: {cur}")
                        break
                    frame.click('button[aria-label="increment Date"]')
                    date_attempts += 1
                    scraper.wait_for_timeout(100)
                except Exception as e:
                    logger.warning(f"SPIN date picker error: {e}")
                    break
            
            if date_attempts >= max_date_attempts:
                logger.warning(f"SPIN date picker reached max attempts, current date: {cur if 'cur' in locals() else 'unknown'}")

            # ---- GUEST PICKER ----
            # decrement to zero
            for _ in range(15):
                try:
                    frame.click('button[aria-label="decrement Guests"]', force=True)
                except:
                    break
                scraper.wait_for_timeout(50)

            # increment to desired
            max_guest_attempts = 20  # Prevent infinite loop
            guest_attempts = 0
            while guest_attempts < max_guest_attempts:
                try:
                    cur_guests = frame.eval_on_selector(
                        'button[data-test="sr-guest-count-button"] div:nth-child(1)',
                        'el => el.textContent.trim()'
                    )
                    if str(cur_guests) == str(guests):
                        logger.info(f"SPIN guests matched: {cur_guests}")
                        break
                    try:
                        frame.click('button[aria-label="increment Guests"]', force=True)
                    except:
                        try:
                            frame.click('button[aria-label="increment Guest"]', force=True)
                        except:
                            logger.warning("SPIN guest increment button not found")
                            break
                    guest_attempts += 1
                    scraper.wait_for_timeout(50)
                except Exception as e:
                    logger.warning(f"SPIN guest picker error: {e}")
                    break
            
            if guest_attempts >= max_guest_attempts:
                logger.warning(f"SPIN guest picker reached max attempts, current guests: {cur_guests if 'cur_guests' in locals() else 'unknown'}")

            # ---- TIME PICKER ----
            normalized_time = normalize_time_value(selected_time)
            if normalized_time:
                frame.wait_for_selector('button[data-test="sr-time-button"]', timeout=8000)
                adjust_picker(
                    frame,
                    'button[data-test="sr-time-button"]',
                    'button[aria-label="increment Time"]',
                    'button[aria-label="decrement Time"]',
                    LAWN_CLUB_TIME_OPTIONS,
                    normalized_time,
                    normalize_time_value
                )
                scraper.wait_for_timeout(200)

            # ---- CLICK SEARCH ----
            try:
                frame.wait_for_selector('button[data-test="sr-search-button"]', timeout=5000, state='visible')
                frame.click('button[data-test="sr-search-button"]', force=True)
                logger.info("SPIN search button clicked")
                scraper.wait_for_timeout(3500)
            except Exception as e:
                logger.warning(f"SPIN Search button click failed: {e}")
                return results

            # ---- SCRAPE AVAILABLE SLOTS ----
            html = frame.content()
            soup = BeautifulSoup(html, "html.parser")

            slot_buttons = soup.select('button[data-test="sr-timeslot-button"]')

            if not slot_buttons:
                logger.info("No SPIN slots found")
                return results

            for btn in slot_buttons:
                try:
                    time_txt = btn.find_all("div")[0].get_text(strip=True)
                except:
                    time_txt = "None"

                try:
                    desc_txt = btn.find_all("div")[1].get_text(strip=True)
                except:
                    desc_txt = "None"

                venue_name = SPIN_VENUE_NAMES.get(location, 'SPIN (NYC)')
                results.append({
                    "date": target_date,
                    "time": time_txt,
                    "price": desc_txt,
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": venue_name
                })

            return results

    except Exception as e:
        logger.error(f"Error scraping SPIN NYC: {e}", exc_info=True)
        return results