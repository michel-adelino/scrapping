"""
Swingers scraper (NYC and London) using Playwright
"""
from datetime import datetime
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

def scrape_swingers(guests, target_date):
    """Swingers NYC scraper function"""
    results = []
    
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        date_str = target_date
        month = dt.month
        year = dt.year
        day = dt.strftime("%d")
        month_abbr = dt.strftime("%b")
        
        query_params = {
            "guests": str(guests),
            "search[month]": str(month),
            "search[year]": str(year),
            "depart": date_str
        }
        
        url = f"https://www.swingers.club/us/locations/nyc/book-now?{urlencode(query_params)}"

        with BaseScraper() as scraper:

            # ---- LOAD PAGE WITH FORCED STOP ----
            try:
                scraper.goto(url, timeout=4000, wait_until="domcontentloaded")
            except:
                pass  # Ignore timeout

            # scraper.wait_for_timeout(5000)  # allow JS to run
            # Stop loading - with error handling for navigation race conditions
            # try:
            #     scraper.page.evaluate("window.stop()")  # STOP loading immediately
            # except Exception as e:
            #     # Page may have navigated away - this is OK, continue
            #     if "Execution context was destroyed" not in str(e) and "navigation" not in str(e).lower():
            #         raise
            #     logger.debug(f"Page navigated during stop() call, continuing: {e}")

            # ---- WAIT FOR CALENDAR RENDER ----
            try:
                scraper.wait_for_selector("li.slot-calendar__dates-item", timeout=10000)
            except:
                logger.warning("Calendar dates not found.")

            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            dates = soup.find_all(
                "li",
                {"class": "slot-calendar__dates-item", "data-available": "true"}
            )

            if not dates:
                return results

            target_li = None
            for d in dates:
                if d.get("data-date") == target_date:
                    target_li = d
                    break

            if not target_li:
                return results

            full_url = "https://www.swingers.club" + target_li.find("a")["href"]
            # ---- LOAD SLOT PAGE WITH FORCED STOP ----
            try:
                scraper.goto(full_url, timeout=5000, wait_until="domcontentloaded")
            except:
                pass

            scraper.wait_for_timeout(4000)
            # scraper.page.evaluate("window.stop()")

            # ---- WAIT FOR SLOTS ----
            try:
                scraper.wait_for_selector("button[data-day]", timeout=2000)
            except:
                logger.warning("Slot buttons not found.")

            # ---- PARSE SLOTS ----
            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            slots = soup.find_all("button", {"data-day": day, "data-month": month_abbr})

            for slot in slots:
                status_el = slot.select_one("div.slot-search-result__low-stock")
                status = status_el.get_text(strip=True) if status_el else "Available"

                time_el = slot.find("span", {"class": "slot-search-result__time h5"})
                time_val = time_el.get_text(strip=True) if time_el else "None"

                price_el = slot.find("span", {"class": "slot-search-result__price-label"})
                price_val = price_el.get_text(strip=True) if price_el else "None"

                slot_data = {
                    "date": target_date,
                    "time": time_val,
                    "price": price_val,
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                    "website": "Swingers (Nomad)"
                }
                results.append(slot_data)

        return results

    except Exception as e:
        logger.error(f"Error scraping Swingers NYC: {e}", exc_info=True)
        raise e

def scrape_swingers_uk(guests, target_date):
    """Swingers UK scraper function"""
    results = []
    
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        date_str = target_date
        month = dt.month
        year = dt.year
        day = dt.strftime("%d")
        month_abbr = dt.strftime("%b")
        
        query_params = {
            "guests": str(guests),
            "search[month]": str(month),
            "search[year]": str(year),
            "depart": date_str
        }
        
        url = f"https://www.swingers.club/uk/book-now?{urlencode(query_params)}"
        
        with BaseScraper() as scraper:

            # ---- LOAD PAGE WITH FORCED STOP ----
            try:
                scraper.goto(url, timeout=4000, wait_until="domcontentloaded")
            except:
                pass  # Ignore timeout

            # scraper.wait_for_timeout(5000)  # allow JS to run
            # scraper.page.evaluate("window.stop()")  # STOP loading immediately

            # ---- WAIT FOR CALENDAR RENDER ----
            try:
                scraper.wait_for_selector("li.slot-calendar__dates-item", timeout=10000)
            except:
                logger.warning("Calendar dates not found.")

            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            dates = soup.find_all(
                "li",
                {"class": "slot-calendar__dates-item", "data-available": "true"}
            )

            if not dates:
                return results

            target_li = None
            for d in dates:
                if d.get("data-date") == target_date:
                    target_li = d
                    break

            if not target_li:
                return results

            full_url = "https://www.swingers.club" + target_li.find("a")["href"]
            # ---- LOAD SLOT PAGE WITH FORCED STOP ----
            try:
                scraper.goto(full_url, timeout=2000, wait_until="domcontentloaded")
            except:
                pass

            scraper.wait_for_timeout(2000)
            scraper.page.evaluate("window.stop()")

            # ---- WAIT FOR SLOTS ----
            try:
                scraper.wait_for_selector("button[data-day]", timeout=2000)
            except:
                logger.warning("Slot buttons not found.")

            # ---- PARSE SLOTS ----
            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            slots = soup.find_all("button", {"data-day": day, "data-month": month_abbr})

            for slot in slots:
                status_el = slot.select_one("div.slot-search-result__low-stock")
                status = status_el.get_text(strip=True) if status_el else "Available"

                time_el = slot.find("span", {"class": "slot-search-result__time h5"})
                time_val = time_el.get_text(strip=True) if time_el else "None"

                price_el = slot.find("span", {"class": "slot-search-result__price-label"})
                price_val = price_el.get_text(strip=True) if price_el else "None"

                slot_data = {
                    "date": target_date,
                    "time": time_val,
                    "price": price_val,
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                    "website": "Swingers (Oxford Circus)"
                }
                results.append(slot_data) 
        return results

    except Exception as e:
        logger.error(f"Error scraping Swingers UK: {e}", exc_info=True)
        raise e