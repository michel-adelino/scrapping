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

# Location IDs for each Five Iron Golf location
# TODO: Update these with the correct location IDs for each location
FIVE_IRON_LOCATION_IDS = {
    'fidi': '4388c520-a4de-4d49-b812-e2cb4badf667',  # Current default
    'flatiron': '31f9eb4b-7fa7-4073-9c36-132b626c8b7e',  # TODO: Update with correct ID
    'grand_central': 'c71d765c-c7fd-4be7-aaba-2f3b21a91ba0',  # TODO: Update with correct ID
    'herald_square': 'd88353cb-4ec3-4477-b9dc-177692591b30',  # TODO: Update with correct ID
    'long_island_city': 'e17214e1-28cb-4170-ab89-ea3532501251',  # TODO: Update with correct ID
    'upper_east_side': '3e7541f4-535a-42ad-b5d2-32bc46ce859e',  # TODO: Update with correct ID
    'rockefeller_center': '610341f5-c98d-4e02-ba7f-0ce46348cd34'  # TODO: Update with correct ID
}

# Venue name mappings for each location
FIVE_IRON_VENUE_NAMES = {
    'fidi': 'Five Iron Golf (Financial District)',
    'flatiron': 'Five Iron Golf (Flatiron)',
    'grand_central': 'Five Iron Golf (Midtown East)',
    'herald_square': 'Five Iron Golf (Herald Square)',
    'long_island_city': 'Five Iron Golf (Long Island City)',
    'upper_east_side': 'Five Iron Golf (Upper East Side)',
    'rockefeller_center': 'Five Iron Golf (Rockefeller Center)'
}


def scrape_five_iron_golf(guests, target_date, location='fidi'):
    """
    Five Iron Golf scraper using DIRECT API (no duplicates).
    Uses locationId = 4388c520-a4de-4d49-b812-e2cb4badf667
    """

    results = []
    unique_set = set()  # prevent duplicates

    # Get the correct venue name based on location parameter
    venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf (Financial District)')
    
    # Get the location-specific location_id
    location_id = FIVE_IRON_LOCATION_IDS.get(location, '31f9eb4b-7fa7-4073-9c36-132b626c8b7e')

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
