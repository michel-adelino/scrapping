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

    #  Import helper functions dynamically
    from app import (
        LAWN_CLUB_TIME_OPTIONS,
        normalize_time_value,
        adjust_picker,
    )

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%a, %b ") + str(dt.day)

        with BaseScraper() as scraper:

            # ---- LOAD ROOT PAGE FAST ----
            # Get URL for the specified location
            base_url = SPIN_URLS.get(location, SPIN_URLS['flatiron'])
            try:
                scraper.goto(
                    base_url
                    + "#elementor-action%3Aaction%3Doff_canvas%3Aopen%26settings%3DeyJpZCI6ImM4OGU1Y2EiLCJkaXNwbGF5TW9kZSI6Im9wZW4ifQ%3D%3D",
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
            # Try multiple selectors for the reservation button
            button_clicked = False
            button_selectors = [
                'div.elementor-element.elementor-element-16e99e3.elementor-widget-button',
                'div.elementor-widget-button a[href*="table-reservations"]',
            ]
            
            # Try text-based selectors using Playwright's text matching
            text_selectors = [
                ('button', 'Reserve'),
                ('a', 'Reserve'),
                ('button', 'Book'),
                ('a', 'Book'),
            ]
            
            for selector in button_selectors:
                try:
                    scraper.page.wait_for_selector(selector, timeout=3000, state='visible')
                    scraper.click(selector)
                    button_clicked = True
                    logger.info(f"SPIN reservation button clicked using selector: {selector}")
                    break
                except:
                    continue
            
            # If CSS selectors didn't work, try text-based matching
            if not button_clicked:
                for tag, text in text_selectors:
                    try:
                        element = scraper.page.locator(f'{tag}:has-text("{text}")').first
                        if element.is_visible(timeout=3000):
                            element.click()
                            button_clicked = True
                            logger.info(f"SPIN reservation button clicked using text: {text}")
                            break
                    except:
                        continue
            
            if not button_clicked:
                logger.warning("SPIN reservation button not found with any selector")
                return results

            scraper.wait_for_timeout(3500)

            # ---- GET SevenRooms Iframe ----
            # Wait for iframe to load with multiple possible selectors
            iframe_handle = None
            iframe_selectors = [
                'iframe[nitro-lazy-src*="sevenrooms.com/reservations/spinyc"]',
                'iframe[src*="sevenrooms.com"]',
                'iframe[nitro-lazy-src*="sevenrooms"]',
            ]
            
            for selector in iframe_selectors:
                try:
                    scraper.page.wait_for_selector(selector, timeout=10000, state='attached')
                    iframe_handle = scraper.page.query_selector(selector)
                    if iframe_handle:
                        logger.info(f"SPIN SevenRooms iframe found using selector: {selector}")
                        break
                except:
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