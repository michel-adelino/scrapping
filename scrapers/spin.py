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
                # Build URL based on location
                if location == 'flatiron':
                    # Flatiron uses the table-reservations path with elementor action
                    url = (
                        f"https://wearespin.com/location/{location_path}/table-reservations/"
                        "#elementor-action%3Aaction%3Doff_canvas%3Aopen%26settings%3DeyJpZCI6ImM4OGU1Y2EiLCJkaXNwbGF5TW9kZSI6Im9wZW4ifQ%3D%3D"
                    )
                else:
                    # Midtown and other locations use the base location URL
                    url = f"https://wearespin.com/location/{location_path}"
                
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

            # ---- CLICK RESERVE BUTTON (Flatiron only) ----
            if location == 'flatiron':
                try:
                    scraper.click(
                        'div.elementor-element.elementor-element-16e99e3.elementor-widget-button'
                    )
                except:
                    logger.warning("SPIN reservation button not found")
                    return results
                scraper.wait_for_timeout(3500)
            else:
                # Midtown: Look for reservation button or widget trigger
                # The iframe might be embedded directly, so we try to find a button but don't fail if not found
                try:
                    clicked = False
                    # Try various selectors for reservation/book buttons
                    selectors = [
                        'a[href*="reservation"]',
                        'a[href*="book"]',
                        '[data-test*="reservation"]',
                        '[data-test*="book"]',
                        'button[class*="reservation"]',
                        'button[class*="book"]',
                        'a[class*="reservation"]',
                        'a[class*="book"]'
                    ]
                    for selector in selectors:
                        try:
                            element = scraper.page.query_selector(selector)
                            if element:
                                element.click()
                                clicked = True
                                logger.info(f"Clicked reservation button for Midtown: {selector}")
                                break
                        except:
                            continue
                    
                    if not clicked:
                        # If no button found, the iframe might already be visible or embedded directly
                        logger.info("No reservation button found for Midtown, iframe may be embedded directly")
                    scraper.wait_for_timeout(3500)
                except Exception as e:
                    logger.warning(f"Could not find reservation button for Midtown: {e}, proceeding anyway")
                    scraper.wait_for_timeout(2000)

            # ---- GET SevenRooms Iframe ----
            try:
                # Try multiple iframe selectors for different locations
                iframe_selectors = [
                    'iframe[nitro-lazy-src*="sevenrooms.com/reservations/spinyc"]',
                    'iframe[src*="sevenrooms.com"]',
                    'iframe[id*="sevenrooms"]',
                    'iframe[data-test*="sevenrooms"]'
                ]
                
                iframe_handle = None
                for selector in iframe_selectors:
                    try:
                        iframe_handle = scraper.page.query_selector(selector)
                        if iframe_handle:
                            break
                    except:
                        continue
                
                if not iframe_handle:
                    logger.warning("SPIN SevenRooms iframe not found")
                    return results

                frame = iframe_handle.content_frame()
            except Exception as e:
                logger.error(f"Could not load iframe: {e}")
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
