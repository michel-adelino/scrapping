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
            try:
                scraper.click(
                    'div.elementor-element.elementor-element-16e99e3.elementor-widget-button'
                )
            except:
                logger.warning("SPIN reservation button not found")
                return results

            scraper.wait_for_timeout(3500)

            # ---- GET SevenRooms Iframe ----
            try:
                iframe_handle = scraper.page.query_selector(
                    'iframe[nitro-lazy-src*="sevenrooms.com/reservations/spinyc"]'
                )
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