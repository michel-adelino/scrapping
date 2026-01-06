"""OpenTable scraper using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

def scrape_tsquaredsocial(guests, target_date, selected_time=None):
    """
    Scrapes available time slots from OpenTable
    """

    results = []

    url = (
        "https://www.opentable.com/booking/restref/availability"
        "?lang=en-US"
        "&restRef=1331374"
        "&otSource=Restaurant%20website"
    )

    try:
        with BaseScraper() as scraper:

            # -------------------------------------------------
            # LOAD PAGE
            # -------------------------------------------------
            scraper.goto(url, timeout=20000, wait_until="domcontentloaded")
            scraper.wait_for_timeout(4000)

            # =================================================
            # SELECT PARTY SIZE (SELECT ELEMENT)
            # =================================================
            try:
                scraper.page.wait_for_selector(
                    'select[data-test="party-size-picker"]',
                    timeout=5000
                )
                scraper.page.select_option(
                    'select[data-test="party-size-picker"]',
                    value=str(guests)
                )
                scraper.wait_for_timeout(600)
            except Exception as e:
                logger.warning(f"⚠️ Party size selection failed: {e}")

            # =================================================
            # SELECT DATE (FINAL FIX)
            # =================================================
            try:
                dt = datetime.strptime(target_date, "%Y-%m-%d")

                target_year = dt.year
                target_month = dt.strftime("%b")        # Dec
                target_day_aria = dt.strftime("%A, %B %-d")  # Friday, December 19

                # Open date picker
                scraper.page.click('div[data-test="day-picker"]')
                scraper.wait_for_timeout(600)

                # Safety: max 12 month navigation
                for _ in range(12):

                    current_label = scraper.page.inner_text(
                        '#dtp-picker-day-picker-label'
                    ).strip()
                    # e.g. "Dec 19, 2025"

                    # Parse visible label
                    # Split → ["Dec", "19,", "2025"]
                    parts = current_label.replace(",", "").split()
                    visible_month = parts[0]    # Dec
                    visible_year = int(parts[2])  # 2025

                    if visible_month == target_month and visible_year == target_year:
                        break

                    scraper.page.click('button[name="next-month"]')
                    scraper.wait_for_timeout(500)

                else:
                    logger.error(f"❌ Target month not reachable: {target_month} {target_year}")
                    return results

                # Click exact day
                scraper.page.click(
                    f'button[name="day"][aria-label="{target_day_aria}"]',
                    timeout=5000
                )
                scraper.wait_for_timeout(600)

            except Exception as e:
                logger.warning(f"⚠️ Date selection failed: {e}")


            # =================================================
            # CLICK "FIND A TABLE"
            # =================================================
            try:
                scraper.page.click(
                    'button[data-test="dtpPicker-submit"]',
                    timeout=8000
                )
            except:
                logger.error("❌ Find a table button not found")
                return results

            # =================================================
            # WAIT FOR SLOT CONTAINER
            # =================================================
            try:
                scraper.page.wait_for_selector(
                    'div[data-test="searched-day-slots"]',
                    timeout=15000
                )
            except:
                logger.warning("⚠️ No slots container found")
                return results

            scraper.wait_for_timeout(2000)

            # =================================================
            # PARSE HTML
            # =================================================
            html = scraper.page.content()

            with open("opentable_debug.html", "w") as f:
                f.write(html)

            soup = BeautifulSoup(html, "html.parser")

            slot_buttons = soup.select(
                'button[data-test="slot-button"]'
            )

            if not slot_buttons:
                logger.info("No OpenTable slots available")
                return results

            # =================================================
            # EXTRACT SLOTS
            # =================================================
            for btn in slot_buttons:
                time_txt = btn.get_text(strip=True)
                aria = btn.get("aria-label", "")

                results.append({
                    "date": target_date,
                    "time": time_txt,
                    "description": aria,
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": "T-Squared Social"
                })

            return results

    except Exception as e:
        logger.error(f"Error scraping OpenTable: {e}", exc_info=True)
        return results
