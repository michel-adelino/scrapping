
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

# ================================================================
# Helper Functions
# ================================================================
def extract_time_from_slot(slot):
    """Extracts event time from Easybowl slot."""
    try:
        event_table = slot.find("table", {"class": "tableEventDetails"})
        if event_table:
            time_rows = event_table.find_all("tr")
            time_info = []
            for row in time_rows:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    event_name = cells[1].get_text(strip=True)
                    start_time = cells[2].get_text(strip=True)
                    end_time = cells[3].get_text(strip=True)
                    if start_time and end_time:
                        time_info.append(f"{event_name}: {start_time} - {end_time}")
            return " | ".join(time_info) if time_info else event_table.get_text(strip=True)
    except:
        pass
    return "None"


def extract_price_from_slot(slot):
    """Extracts pricing info from Easybowl slot."""
    try:
        price_table = slot.find("table", {"class": "tablePriceBox"})
        if price_table:
            price_rows = price_table.find_all("tr")
            price_info = []
            for row in price_rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    label = cells[0].get_text(strip=True)
                    value = cells[2].get_text(strip=True)
                    if label and value:
                        price_info.append(f"{label}: {value}")
            return " | ".join(price_info) if price_info else price_table.get_text(strip=True)
    except:
        pass
    return "None"


def get_product_name(slot):
    name_el = slot.select_one("div.prodHeadline")
    return name_el.get_text(strip=True) if name_el else "Unknown"


# ================================================================
# Main Scraper
# ================================================================
def scrape_easybowl(guests, target_date):
    """Easybowl NYC scraper function"""
    results = []

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        easybowl_date = dt.strftime("d-%d-%m-%Y")

        url = "https://www.easybowl.com/bc/LET/booking"

        with BaseScraper() as scraper:
            scraper.page.set_default_timeout(60000)

            print("[DEBUG] Loading Easybowl...")
            try:
                # scraper.goto(url, timeout=4000, wait_until="domcontentloaded")
                scraper.goto(url, timeout=60000, wait_until="load")
            except:
                pass

            # scraper.page.evaluate("window.stop()")
            scraper.wait_for_timeout(1200)

            print(f"[DEBUG] Looking for date cell: {easybowl_date}")

            # === Calendar Navigation ===
            for attempt in range(1, 30):
                print(f"[DEBUG] Calendar Loop Iteration: {attempt}")
                try:
                    scraper.click(f"td#{easybowl_date}")
                    print("[DEBUG] Date found and clicked!")
                    break
                except:
                    scraper.click("//a[normalize-space()='>>']")
                    scraper.wait_for_timeout(400)

            print("[DEBUG] Selecting guests:", guests)
            scraper.select_option("//select[@id='adults']", str(guests))

            scraper.click("//div[normalize-space()='Search']")
            scraper.wait_for_timeout(2500)

            print("[DEBUG] Searching product groups...")

            # ================================================================
            # OUTER PRODUCT GROUP LOOP
            # ================================================================
            group_iteration = 0

            while True:
                group_iteration += 1
                print(f"\n[DEBUG] OUTER GROUP LOOP #{group_iteration}")

                # 🔥 FIX → stop after 1 cycle
                if group_iteration > 1:
                    print("[DEBUG] All groups processed once → Stopping loop.")
                    break

                content = scraper.get_content()
                soup = BeautifulSoup(content, "html.parser")

                groups = scraper.page.locator("//div[@class='button prodGroupButton']").all()
                print(f"[DEBUG] Found {len(groups)} outer groups")

                if not groups:
                    print("[DEBUG] No groups found → stopping.")
                    break


                # ================================================================
                # PROCESS EACH OUTER GROUP
                # ================================================================
                for j in range(len(groups)):
                    print(f"\n[DEBUG] Clicking Outer Group #{j+1}/{len(groups)}")
                    groups = scraper.page.locator("//div[@class='button prodGroupButton']").all()
                    groups[j].click()
                    scraper.wait_for_timeout(900)

                    content = scraper.get_content()
                    soup = BeautifulSoup(content, "html.parser")

                    nested_groups = soup.find_all("div", {"class": "prodBox prodGroup"})
                    print(f"[DEBUG] Found {len(nested_groups)} nested groups")

                    # ================================================================
                    # NESTED GROUPS
                    # ================================================================
                    if nested_groups:
                        nested_buttons = scraper.page.locator("//div[@class='button prodGroupButton']").all()

                        for k in range(len(nested_buttons)):
                            print(f"[DEBUG] Clicking Nested Group #{k+1}/{len(nested_buttons)}")

                            nested_buttons = scraper.page.locator("//div[@class='button prodGroupButton']").all()
                            nested_buttons[k].click()
                            scraper.wait_for_timeout(900)

                            content = scraper.get_content()
                            soup = BeautifulSoup(content, "html.parser")

                            slots = soup.find_all("div", {"class": "prodBox"})
                            actual_products = [p for p in slots if "prodGroup" not in p.get("class", [])]

                            print(f"[DEBUG] Nested products found: {len(actual_products)}")

                            for slot in actual_products:
                                name = get_product_name(slot)
                                print(f"[DEBUG] Nested Product Name: {name}")

                                time = extract_time_from_slot(slot)
                                price = extract_price_from_slot(slot)

                                results.append({
                                    "date": target_date,
                                    "time": time,
                                    "price": price,
                                    "status": name,
                                    "timestamp": datetime.now().isoformat(),
                                    "website": "Frames Bowling Lounge (Midtown)"
                                })

                            print("[DEBUG] Going BACK from nested product page")
                            scraper.page.go_back()
                            scraper.wait_for_timeout(700)

                    # ================================================================
                    # DIRECT PRODUCTS
                    # ================================================================
                    else:
                        print("[DEBUG] No nested groups → Direct Product Page")

                        slots = soup.find_all("div", {"class": "prodBox"})
                        actual_products = [p for p in slots if "prodGroup" not in p.get("class", [])]
                        print(f"[DEBUG] Direct products found: {len(actual_products)}")

                        for slot in actual_products:
                            name = get_product_name(slot)
                            print(f"[DEBUG] Direct Product Name: {name}")

                            time = extract_time_from_slot(slot)
                            price = extract_price_from_slot(slot)

                            results.append({
                                "date": target_date,
                                "time": time,
                                "price": price,
                                "status": name,
                                "timestamp": datetime.now().isoformat(),
                                "website": "Frames Bowling Lounge (Midtown)"
                            })

                    print("[DEBUG] Going BACK from group page")
                    scraper.page.go_back()
                    scraper.wait_for_timeout(700)

            print(f"[DEBUG] TOTAL RESULTS FOUND: {len(results)}")
            return results

    except Exception as e:
        print(f"[DEBUG] ERROR: {e}")
        raise
