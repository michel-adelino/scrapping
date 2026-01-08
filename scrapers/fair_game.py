"""Fair Game scraper (Canary Wharf and City) using Playwright"""
import re
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


def parse_fair_game_slots(html, venue_name, target_date, results, guests, booking_url_base):
    """Shared parser for both Fair Game City & Canary Wharf"""
    soup = BeautifulSoup(html, "html.parser")

    # Find all reservation buttons
    slots = soup.find_all(
        "button",
        attrs={"data-test": re.compile("reservation-timeslot-button")}
    )

    logger.info(f"[{venue_name}] Found {len(slots)} time slots")

    if not slots:
        return results

    for slot in slots:
        # Extract time
        try:
            time_text = slot.find(
                "span",
                {"data-test": "reservation-timeslot-button-time"}
            ).get_text(strip=True)
        except:
            time_text = "None"

        # Extract description text
        try:
            desc = slot.find(
                "span",
                {"data-test": "reservation-timeslot-button-description"}
            ).get_text(strip=True)
        except:
            desc = "None"

        # Construct booking URL with date and party_size
        booking_url = f"{booking_url_base}?date={target_date}&party_size={guests}"

        results.append({
            "date": target_date,
            "time": time_text,
            "price": desc,
            "status": "Available",
            "timestamp": datetime.now().isoformat(),
            "website": venue_name,
            "booking_url": booking_url,
        })

    return results


# ------------------------------------------------------------------------------
#            FAIR GAME CANARY WHARF
# ------------------------------------------------------------------------------

def scrape_fair_game_canary_wharf(guests, target_date):
    """Fair Game Canary Wharf scraper using Playwright"""
    results = []
    venue_name = "Fair Game (Canary Wharf)"

    try:
        with BaseScraper() as scraper:
            logger.info(f"[{venue_name}] Loading page...")

            url = (
                "https://www.sevenrooms.com/explore/fairgame/"
                f"reservations/create/search?date={target_date}&party_size={guests}"
            )

            scraper.goto(url, timeout=60000, wait_until="domcontentloaded")
            # scraper.goto(url, timeout=4000, wait_until="domcontentloaded")
            # scraper.page.evaluate("window.stop()")  # STOP loading immediately
            scraper.wait_for_timeout(3500)

            html = scraper.get_content()

            booking_url_base = "https://www.sevenrooms.com/explore/fairgame/reservations/create/search"
            results = parse_fair_game_slots(html, venue_name, target_date, results, guests, booking_url_base)

        return results

    except Exception as e:
        logger.error(f"Error scraping {venue_name}: {e}", exc_info=True)
        return results


# ------------------------------------------------------------------------------
#            FAIR GAME CITY
# ------------------------------------------------------------------------------

def scrape_fair_game_city(guests, target_date):
    """Fair Game City scraper using Playwright"""
    results = []
    venue_name = "Fair Game (City)"

    try:
        with BaseScraper() as scraper:
            logger.info(f"[{venue_name}] Loading page...")

            url = (
                "https://www.sevenrooms.com/explore/fairgamecity/"
                f"reservations/create/search/?date={target_date}&party_size={guests}"
            )

            scraper.goto(url, timeout=60000, wait_until="domcontentloaded")
            scraper.wait_for_timeout(3500)

            html = scraper.get_content()

            booking_url_base = "https://www.sevenrooms.com/explore/fairgamecity/reservations/create/search"
            results = parse_fair_game_slots(html, venue_name, target_date, results, guests, booking_url_base)

        return results

    except Exception as e:
        logger.error(f"Error scraping {venue_name}: {e}", exc_info=True)
        return results
