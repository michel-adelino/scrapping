"""Lucky Strike NYC scraper using Playwright"""
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# Lucky Strike location mappings
LUCKY_STRIKE_LOCATIONS = {
    'chelsea_piers': 'lucky-strike-chelsea-piers',
    'times_square': 'lucky-strike-times-square'
}

# Venue name mappings for each location
LUCKY_STRIKE_VENUE_NAMES = {
    'chelsea_piers': 'Lucky Strike (Chelsea Piers)',
    'times_square': 'Lucky Strike (Times Square)'
}

def scrape_lucky_strike(guests, target_date, location='chelsea_piers'):
    """Lucky Strike NYC scraper function"""
    results = []
    
    try:
        date_str = target_date
        dt = datetime.strptime(date_str, "%Y-%m-%d")

        # Get location slug from mapping
        location_slug = LUCKY_STRIKE_LOCATIONS.get(location, 'lucky-strike-chelsea-piers')
        venue_name = LUCKY_STRIKE_VENUE_NAMES.get(location, 'Lucky Strike (Chelsea Piers)')

        url = (
            f"https://www.luckystrikeent.com/location/{location_slug}/"
            f"booking/lane-reservation?date={target_date}T23:00:00.000Z&guestsCount={guests}"
        )

        logger.info(f"[LuckyStrike] Navigating to: {url} (location: {location})")

        with BaseScraper() as scraper:
            scraper.page.set_default_timeout(60000)

            # Load quickly then stop heavy JS loading
            try:
                scraper.goto(url, timeout=10000, wait_until="domcontentloaded")
            except:
                pass

            # scraper.page.evaluate("window.stop()")   # Immediately stop loading
            scraper.wait_for_timeout(1500)

            # Wait for time slots container
            try:
                scraper.wait_for_selector('button.TimeSlotSelection_timeSlot__hxKpB', timeout=15000)
            except:
                logger.warning("No slots found on Lucky Strike")
                return results

            # Get page HTML
            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            # Extract slots
            slots = soup.select("button.TimeSlotSelection_timeSlot__hxKpB")
            logger.info(f"[LuckyStrike] Found {len(slots)} slots")

            if not slots:
                return results

            for slot in slots:
                # TIME
                try:
                    time_val = slot.find_all("span")[0].get_text(strip=True)
                except:
                    time_val = "None"

                # DESCRIPTION
                try:
                    desc = slot.find_all("span")[1].get_text(strip=True)
                except:
                    desc = "None"

                results.append({
                    "date": date_str,
                    "time": time_val,
                    "price": desc,
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": venue_name
                })

        return results

    except Exception as e:
        logger.error(f"Error scraping Lucky Strike: {e}", exc_info=True)
        raise e

