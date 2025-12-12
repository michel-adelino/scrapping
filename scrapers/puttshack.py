"""Puttshack scraper using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


def scrape_puttshack(location, guests, target_date):
    """Puttshack scraper (Playwright version)"""
    results = []

    print("\n==================== PUTTSHACK PLAYWRIGHT ====================\n")
    print(f"[DEBUG] Location: {location}")
    print(f"[DEBUG] Guests: {guests}")
    print(f"[DEBUG] Date: {target_date}")

    try:
        with BaseScraper() as scraper:

            # ------------------------------------------------------------
            # OPEN PAGE
            # ------------------------------------------------------------
            print("[DEBUG] Opening booking page...")
            scraper.goto("https://www.puttshack.com/book-golf", timeout=60000)
            scraper.wait_for_timeout(4000)

            # ------------------------------------------------------------
            # CLOSE POPUPS (GetSiteControl widget)
            # ------------------------------------------------------------
            scraper.page.evaluate("""
                () => {
                    let widget = document.getElementById('getsitecontrol-518774');
                    if(widget) widget.remove();

                    document.querySelectorAll('getsitecontrol-widget')
                        .forEach(w => w.remove());
                }
            """)
            scraper.wait_for_timeout(500)

            # ------------------------------------------------------------
            # COUNTRY SELECT
            # ------------------------------------------------------------
            print("[DEBUG] Selecting country...")
            scraper.click('button.input-button.svelte-9udp5p')
            scraper.click('div[data-label="United Kingdom"]')
            scraper.wait_for_timeout(1000)

            # ------------------------------------------------------------
            # VENUE SELECT
            # ------------------------------------------------------------
            print("[DEBUG] Selecting venue:", location)
            scraper.click('button[aria-label="Venue Selector"]')

            venue_btn = scraper.page.locator(
                f"//div[contains(text(),'{location}')]"
            ).first

            venue_btn.click()
            scraper.wait_for_timeout(1000)

            # ------------------------------------------------------------
            # DATE SELECT
            # ------------------------------------------------------------
            print("[DEBUG] Opening date selector...")
            scraper.click('button[aria-label="Date Selector"]')

            scraper.wait_for_timeout(1500)

            # Go back 2 months (matches your Selenium version)
            scraper.click('button[aria-label="Previous"]')
            scraper.click('button[aria-label="Previous"]')

            # Loop forward until date found
            print("[DEBUG] Navigating months to reach target:", target_date)

            while True:
                try:
                    scraper.click(f'button[data-value="{target_date}"]')
                    print("[DEBUG] Date selected:", target_date)
                    break
                except:
                    try:
                        scraper.click('button[aria-label="Next"]')
                    except:
                        print("[ERROR] Could not click NEXT in calendar")
                        break

            scraper.wait_for_timeout(1500)

            # ------------------------------------------------------------
            # PLAYER COUNT
            # ------------------------------------------------------------
            print("[DEBUG] Selecting players:", guests)
            scraper.click('button[aria-label="Player Selector"]')
            scraper.wait_for_timeout(1000)

            while True:
                # read current value
                current = scraper.page.evaluate("""
                    () => {
                        let t = document.querySelector('.count.svelte-1v5dv5l');
                        return t ? parseInt(t.textContent.trim()) : null;
                    }
                """)
                print("[DEBUG] Current players:", current)

                if current == guests:
                    break

                # Increase
                scraper.click("button[aria-label='Increase player count']", timeout=2000)

                scraper.wait_for_timeout(300)

            scraper.wait_for_timeout(800)

            # ------------------------------------------------------------
            # SEARCH FOR TIME
            # ------------------------------------------------------------
            print("[DEBUG] Clicking Find a time...")
            scraper.click('button[aria-label="Find a time"]')
            scraper.wait_for_timeout(5000)

            # Sometimes they show session type
            try:
                choose_btn = scraper.page.locator(
                    "//button[contains(@data-ps-event,'click|handleRoute')]"
                ).first

                if choose_btn.is_visible():
                    print("[DEBUG] Selecting session type...")
                    choose_btn.click()
                    scraper.wait_for_timeout(5000)

            except:
                pass

            print("[DEBUG] Parsing slots...")

            html = scraper.get_content()
            soup = BeautifulSoup(html, "html.parser")

            slot_buttons = soup.select("button.timeslot.svelte-1ihytzt")

            print(f"[DEBUG] Found {len(slot_buttons)} slot buttons")

            for slot in slot_buttons:
                classes = slot.get("class")

                if "disabled" in classes:
                    continue

                # extract time
                time = slot.get_text(strip=True)

                try:
                    desc = slot.find(
                        "span",
                        {"class": "adults svelte-1ihytzt"}
                    ).get_text(strip=True)
                except:
                    desc = "None"

                results.append({
                    "date": target_date,
                    "time": time,
                    "price": desc,
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": f"Puttshack ({location})"
                })

            print(f"✓ SUCCESS — Found {len(results)} slots")

            return results

    except Exception as e:
        print("[ERROR] Puttshack scraper failure:", e)
        return results


