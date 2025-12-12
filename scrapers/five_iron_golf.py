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


def scrape_five_iron_golf(guests, target_date, location='fidi'):
    """
    Five Iron Golf scraper using DIRECT API (no duplicates).
    Uses locationId = 4388c520-a4de-4d49-b812-e2cb4badf667
    """

    results = []
    unique_set = set()  # prevent duplicates

    # location_id = "4388c520-a4de-4d49-b812-e2cb4badf667"
    location_id = "31f9eb4b-7fa7-4073-9c36-132b626c8b7e"
    venue_name = "Five Iron Golf (Custom Location)"

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        api_date = dt.strftime("%Y-%m-%d")

        with BaseScraper() as scraper:
            page = scraper.page

            # try:
            #     scraper.goto("https://booking.fiveirongolf.com", timeout=5000, wait_until="domcontentloaded")
            # except:
            #     pass

            api_url = (
                "https://api.booking.fiveirongolf.com/appointments/available/simulator"
                f"?locationId={location_id}"
                f"&partySize={guests}"
                f"&startDateTime={api_date}"
                f"&endDateTime={api_date}"
            )

            print("[DEBUG] API URL:", api_url)

            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "origin": "https://booking.fiveirongolf.com",
                "referer": "https://booking.fiveirongolf.com/",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "x-variant": "fiveIron",
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "user-agent": (
                    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36"
                ),
            }

            resp = page.request.get(api_url, headers=headers, timeout=30000)
            data = resp.json()

            print(f"[DEBUG] API returned {len(data)} entries")

            for entry in data:
                raw_time = entry.get("time")

                try:
                    dt2 = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                    time_str = dt2.strftime("%I:%M %p")
                except:
                    time_str = "N/A"

                for block in entry.get("availabilities", []):
                    for d in block.get("durations", []):
                        mins = d.get("duration", 0)
                        cost = d.get("cost", 0)

                        hours = mins / 60
                        dur_str = f"{int(hours)}h" if hours.is_integer() else f"{hours}h"

                        # Deduplication key
                        key = (time_str, dur_str, cost)

                        if key in unique_set:
                            continue
                        unique_set.add(key)

                        results.append({
                            "date": target_date,
                            "time": time_str,
                            "price": f"{dur_str} : ${cost}",
                            "status": "Available",
                            "timestamp": datetime.now().isoformat(),
                            "website": venue_name
                        })

        return results

    except Exception as e:
        logger.error(f"Error scraping Five Iron Golf: {e}", exc_info=True)
        raise e
