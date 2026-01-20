"""Flight Club Darts scraper using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


def scrape_flight_club_darts(guests, target_date, venue_id=None):
    """
    Flight Club Darts scraper (Playwright version)
    - Scrapes ALL 4 locations from one page
    - Returns slots with correct venue names for each location
    - If venue_id is provided, only scrapes that specific venue (backward compatibility)
    """

    results = []

    print("\n==================== FLIGHT CLUB DARTS (PLAYWRIGHT) ====================\n")
    print(f"[DEBUG] Guests = {guests}")
    print(f"[DEBUG] Date   = {target_date}")
    print(f"[DEBUG] Venue  = {venue_id or 'ALL (scraping all 4 locations)'}")

    # -------------------------
    # Map section titles to venue names
    # -------------------------
    section_to_venue_map = {
        "Bloomsbury, London": "Flight Club Darts (Bloomsbury)",
        "Angel, London": "Flight Club Darts (Angel)",
        "Shoreditch, London": "Flight Club Darts (Shoreditch)",
        "Victoria, London": "Flight Club Darts (Victoria)"
    }

    # For backward compatibility, if venue_id is provided, map it
    if venue_id:
        venue_id_to_section = {
            "1": "Bloomsbury, London",
            "2": "Angel, London",
            "3": "Shoreditch, London",
            "4": "Victoria, London"
        }
        expected_section = venue_id_to_section.get(venue_id)
    else:
        expected_section = None  # Scrape all sections

    # -------------------------
    # Build URL (no venue_id in URL to get all venues)
    # -------------------------
    url = (
        f"https://flightclubdarts.com/book?"
        f"date={target_date}&group_size={guests}"
        f"&preferedtime=11%3A30"
    )
    if venue_id:
        url += f"&preferedvenue={venue_id}"

    print("[DEBUG] URL =", url)

    try:
        with BaseScraper() as scraper:

            print("[DEBUG] Opening booking page...")
            scraper.goto(url, timeout=60000, wait_until="domcontentloaded")
            scraper.wait_for_timeout(10000)

            # -------------------------------------------------------
            # PARSE PAGE
            # -------------------------------------------------------
            html = scraper.get_content()
            soup = BeautifulSoup(html, "html.parser")

            holders = soup.select("div.fc_dmnbook-availability")

            print(f"[DEBUG] Found {len(holders)} venue availability sections")

            if not holders:
                print("❌ No availability sections found.")
                return results

            # -------------------------------------------------------
            # LOOP VENUE SECTIONS - Process ALL locations
            # -------------------------------------------------------
            for holder in holders:

                # Extract venue section title
                try:
                    title_el = holder.find(
                        "span", {"id": "fc_dmnbook-availability__name"}
                    )
                    section_title = title_el.get_text(strip=True) if title_el else "Unknown Venue"
                except:
                    section_title = "Unknown Venue"

                # If filtering by venue_id, skip non-matching sections
                if expected_section and section_title != expected_section:
                    print(f"[DEBUG] Skipping section: {section_title} (not matching {expected_section})")
                    continue

                # Only process sections that are in our allowed list (the 4 specific locations)
                if section_title not in section_to_venue_map:
                    print(f"[DEBUG] Skipping section: {section_title} (not in allowed locations list)")
                    continue

                # Map section title to venue name (guaranteed to exist due to check above)
                venue_name = section_to_venue_map[section_title]

                print(f"\n=== SECTION: {section_title} -> Venue: {venue_name} ===")

                slots = holder.find_all(
                    "div", {"class": "fc_dmnbook-availability-tablecell"}
                )
                print(f"[DEBUG] Raw slots found: {len(slots)}")

                # -------------------------
                # Extract each slot
                # -------------------------
                for slot in slots:

                    # ------- Time -------
                    try:
                        time_val = slot.find(
                            "div",
                            {"class": "fc_dmnbook-availibility__time font-small"},
                        ).get_text(strip=True)
                    except:
                        time_val = "None"

                    # ------- Description -------
                    try:
                        desc = (
                            slot.find("div", {"class": "fc_dmnbook-time_wrapper"})
                            .get_text(strip=True)
                            .replace("\n", " | ")
                        )
                    except:
                        desc = "None"

                    slot_data = {
                        "website": venue_name,  # Use 'website' key to match expected format
                        "date": target_date,
                        "time": time_val,
                        "price": desc,
                        "status": "Available",
                        "timestamp": datetime.now().isoformat(),
                        "booking_url": url
                    }

                    results.append(slot_data)

        print("\n============== FINAL RESULT ==============")
        print(f"Total Slots Found: {len(results)}")
        print("==========================================\n")

        return results

    except Exception as e:
        print("[ERROR] Flight Club Darts scraper failed:", e)
        logger.error(f"Error scraping Flight Club Darts: {e}", exc_info=True)
        return results

