"""
Topgolf Chigwell SevenRooms scraper (direct URL based)
"""

from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


"""
Topgolf Chigwell SevenRooms scraper (FIXED selectors)
"""

from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


def scrape_topgolf_chigwell(guests, target_date, start_time=None):
    from datetime import datetime
    from bs4 import BeautifulSoup
    from urllib.parse import urlencode

    results = []

    params = {
        "date": target_date,
        "party_size": str(guests)
    }
    if start_time:
        params["start_time"] = start_time

    search_url = (
        "https://www.sevenrooms.com/explore/"
        "topgolfchigwell/reservations/create/search?"
        + urlencode(params)
    )

    with BaseScraper() as scraper:

        # ✅ DO NOT USE networkidle
        scraper.goto(
            search_url,
            timeout=60000,
            wait_until="domcontentloaded"
        )

        # small settle delay
        scraper.wait_for_timeout(3000)

        # ✅ WAIT ONLY FOR REAL DOM
        scraper.page.wait_for_selector(
            'div[data-test="reservation-availability-grid-primary"]',
            timeout=30000
        )

        html = scraper.get_content()
        soup = BeautifulSoup(html, "html.parser")

        slot_buttons = soup.select(
            'button[data-test^="reservation-timeslot-button-"]'
        )

        if not slot_buttons:
            return results

        for btn in slot_buttons:
            time_el = btn.select_one(
                'span[data-test="reservation-timeslot-button-time"]'
            )
            price_el = btn.select_one(
                'span[data-test="reservation-timeslot-button-description"]'
            )

            results.append({
                "date": target_date,
                "time": time_el.get_text(strip=True) if time_el else None,
                "price": price_el.get_text(strip=True) if price_el else None,
                "status": "Available",
                "timestamp": datetime.now().isoformat(),
                "website": "Topgolf Chigwell",
                "booking_url": search_url
            })

    return results
