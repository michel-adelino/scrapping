"""SPIN NYC scraper using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

# SPIN location mappings
SPIN_LOCATIONS = {
    'flatiron': 'new-york-flatiron',
    'midtown': 'new-york-midtown'
}

# Venue name mappings for each location
SPIN_VENUE_NAMES = {
    'flatiron': 'SPIN (NYC - Flatiron)',
    'midtown': 'SPIN (NYC - Midtown)'
}


def scrape_spin(guests, target_date, selected_time=None, location='flatiron'):
    """SPIN NYC scraper function (Playwright version)
    
    Args:
        guests: Number of guests
        target_date: Target date in YYYY-MM-DD format
        selected_time: Optional time preference
        location: Location identifier ('flatiron' or 'midtown'), defaults to 'flatiron'
    """

    results = []

    #  Import helper functions dynamically
    from app import (
        LAWN_CLUB_TIME_OPTIONS,
        normalize_time_value,
        adjust_picker,
    )

    # Get the correct venue name and URL path based on location parameter
    venue_name = SPIN_VENUE_NAMES.get(location, 'SPIN (NYC - Flatiron)')
    location_path = SPIN_LOCATIONS.get(location, 'new-york-flatiron')

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%a, %b ") + str(dt.day)

        with BaseScraper() as scraper:

            # ---- LOAD ROOT PAGE FAST ----
            try:
                # Both locations use the table-reservations path                
                url = f"https://wearespin.com/location/{location_path}/table-reservations/"
                
                scraper.goto(
                    url,
                    timeout=6000,
                    wait_until="domcontentloaded"
                )
            except:
                pass

            # scraper.page.evaluate("window.stop()")
            scraper.wait_for_timeout(1000)

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

            scraper.wait_for_timeout(1500)

            # ---- CLICK RESERVE BUTTON ----
            # Both locations use Elementor buttons, try multiple selectors
            try:
                clicked = False
                
                # First, try Playwright locator API with text-based selectors (works for both locations)
                try:
                    # Try text-based locators (most reliable, works for both flatiron and midtown)
                    # Button text is "RESERVE NOW" not "BOOK NOW"
                    reserve_now_locator = scraper.page.locator('a:has-text("RESERVE NOW"), button:has-text("RESERVE NOW")').first
                    if reserve_now_locator.is_visible(timeout=3000):
                        reserve_now_locator.click()
                        clicked = True
                        logger.info(f"Clicked SPIN reservation button ({location}) via text locator")
                except Exception as e:
                    logger.debug(f"Text locator failed: {e}")
                
                # If text locator didn't work, try CSS selectors
                if not clicked:
                    selectors = [
                        # Links to SevenRooms (most reliable)
                        'a[href*="sevenrooms"]',
                        # Elementor button selectors (generic - works for both locations)
                        'div.elementor-widget-button a.elementor-button',
                        'div.elementor-widget-button button.elementor-button',
                        'a.elementor-button-link',
                        'button.elementor-button',
                        # More specific elementor selectors
                        'div.elementor-element.elementor-widget-button a',
                        'div.elementor-element.elementor-widget-button button',
                        # Location-specific selectors (old - kept for backward compatibility)
                        'div.elementor-element.elementor-element-16e99e3.elementor-widget-button',  # Flatiron
                    ]
                    
                    for selector in selectors:
                        try:
                            # Try locator API first
                            try:
                                element = scraper.page.locator(selector).first
                                if element.is_visible(timeout=2000):
                                    element.click()
                                    clicked = True
                                    logger.info(f"Clicked SPIN reservation button ({location}): {selector}")
                                    break
                            except:
                                # Fallback to query_selector
                                element = scraper.page.query_selector(selector)
                                if element:
                                    # Check if visible
                                    is_visible = scraper.page.evaluate("""
                                        (el) => {
                                            const style = window.getComputedStyle(el);
                                            return style.display !== 'none' && 
                                                   style.visibility !== 'hidden' && 
                                                   style.opacity !== '0' &&
                                                   el.offsetParent !== null;
                                        }
                                    """, element)
                                    if is_visible:
                                        element.click()
                                        clicked = True
                                        logger.info(f"Clicked SPIN reservation button ({location}): {selector}")
                                        break
                        except Exception as e:
                            logger.debug(f"Selector {selector} failed: {e}")
                            continue
                
                # Last resort: JavaScript search for any element containing "RESERVE NOW" or similar text
                if not clicked:
                    try:
                        clicked = scraper.page.evaluate("""
                            () => {
                                // Find all clickable elements
                                const elements = Array.from(document.querySelectorAll('a, button, div[role="button"]'));
                                
                                // Look for "RESERVE NOW" text (case insensitive) - primary text on SPIN site
                                const reserveNow = elements.find(el => {
                                    const text = el.textContent.trim().toUpperCase();
                                    return (text.includes('RESERVE NOW') || 
                                            text.includes('RESERVE') ||
                                            text.includes('BOOK NOW') ||
                                            text.includes('BOOK A TABLE')) &&
                                           el.offsetParent !== null; // Element is visible
                                });
                                
                                if (reserveNow) {
                                    // Scroll into view first
                                    reserveNow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                    // Small delay
                                    setTimeout(() => {
                                        reserveNow.click();
                                    }, 100);
                                    return true;
                                }
                                return false;
                            }
                        """)
                        if clicked:
                            logger.info(f"Clicked SPIN reservation button ({location}) via JavaScript text search")
                            scraper.wait_for_timeout(500)  # Wait for click to register
                        else:
                            logger.warning(f"SPIN reservation button not found for {location}")
                            return results
                    except Exception as e:
                        logger.warning(f"JavaScript fallback failed for {location}: {e}")
                        return results
                
                scraper.wait_for_timeout(3500)
            except Exception as e:
                logger.warning(f"Could not click reservation button for {location}: {e}")
                return results

            # ---- GET SevenRooms Iframe ----
            try:
                # Try multiple iframe selectors for different locations
                # Flatiron uses: spinyc, Midtown uses: spinmidtown
                iframe_selectors = [
                    'iframe[nitro-lazy-src*="sevenrooms.com/reservations/spinyc"]',  # Flatiron
                    'iframe[nitro-lazy-src*="sevenrooms.com/reservations/spinmidtown"]',  # Midtown
                    'iframe[src*="sevenrooms.com/reservations/spinyc"]',  # Flatiron (loaded)
                    'iframe[src*="sevenrooms.com/reservations/spinmidtown"]',  # Midtown (loaded)
                    'iframe[nitro-lazy-src*="sevenrooms.com"]',  # Generic
                    'iframe[src*="sevenrooms.com"]',  # Generic (loaded)
                    'iframe[id*="sevenrooms"]',
                    'iframe[data-test*="sevenrooms"]'
                ]
                
                iframe_handle = None
                for selector in iframe_selectors:
                    try:
                        iframe_handle = scraper.page.query_selector(selector)
                        if iframe_handle:
                            logger.info(f"Found SPIN iframe ({location}): {selector}")
                            break
                    except:
                        continue
                
                if not iframe_handle:
                    logger.warning(f"SPIN SevenRooms iframe not found for {location}")
                    return results

                frame = iframe_handle.content_frame()
            except Exception as e:
                logger.error(f"Could not load iframe for {location}: {e}")
                return results

            # ---- DATE PICKER ----
            try:
                frame.wait_for_selector('button[data-test="sr-calendar-date-button"]', timeout=15000)
            except:
                logger.warning("SPIN date button not found")
                return results

            # increment date until matches
            while True:
                cur = frame.eval_on_selector(
                    'button[data-test="sr-calendar-date-button"] div:nth-child(1)',
                    'el => el.textContent.trim()'
                )
                if cur == formatted_date:
                    break
                try:
                    frame.click('button[aria-label="increment Date"]')
                except:
                    break
                scraper.wait_for_timeout(100)

            # ---- GUEST PICKER ----
            # decrement to zero
            for _ in range(15):
                try:
                    frame.click('button[aria-label="decrement Guests"]', force=True)
                except:
                    break
                scraper.wait_for_timeout(50)

            # increment to desired
            while True:
                cur_guests = frame.eval_on_selector(
                    'button[data-test="sr-guest-count-button"] div:nth-child(1)',
                    'el => el.textContent.trim()'
                )
                if str(cur_guests) == str(guests):
                    break
                try:
                    frame.click('button[aria-label="increment Guests"]', force=True)
                except:
                    try:
                        frame.click('button[aria-label="increment Guest"]', force=True)
                    except:
                        break
                scraper.wait_for_timeout(50)

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
                frame.click('button[data-test="sr-search-button"]', force=True)
                scraper.wait_for_timeout(3500)
            except:
                logger.warning("SPIN Search button click failed")
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
                    # Extract time from first direct child div
                    # Structure for both Midtown and Flatiron: 
                    # <button><div>time</div><div>description</div></button>
                    direct_divs = btn.find_all("div", recursive=False)
                    if direct_divs:
                        time_txt = direct_divs[0].get_text(strip=True)
                    else:
                        time_txt = "None"
                except Exception as e:
                    logger.debug(f"Error extracting time: {e}")
                    time_txt = "None"

                try:
                    # Extract description/price from second direct child div
                    direct_divs = btn.find_all("div", recursive=False)
                    if len(direct_divs) > 1:
                        desc_txt = direct_divs[1].get_text(strip=True)
                    else:
                        desc_txt = "None"
                except Exception as e:
                    logger.debug(f"Error extracting description: {e}")
                    desc_txt = "None"

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
        logger.error(f"Error scraping SPIN {location}: {e}", exc_info=True)
        return results
