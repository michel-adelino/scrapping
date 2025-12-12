"""Clays Bar scraper using Playwright (FULLY FIXED VERSION)"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)


def scrape_clays_bar(location, guests, target_date):
    """Clays Bar scraper with EXACT SeleniumBase behaviour ported to Playwright."""
    results = []
    venue_name = f"Clays Bar ({location})"

    print("\n==================== CLAYS BAR PLAYWRIGHT (FIXED) ====================\n")

    # --- DATE PREP ---
    date_obj = datetime.strptime(target_date, "%Y-%m-%d")
    target_month_year = date_obj.strftime("%B %Y")

    try:
        day_num = date_obj.strftime("%-d")  # linux
    except:
        day_num = date_obj.strftime("%#d")  # windows

    target_date_label = f"{date_obj.strftime('%B')} {day_num}, {date_obj.year}"

    print(f"[DEBUG] target_month_year = {target_month_year}")
    print(f"[DEBUG] target_date_label = {target_date_label}")

    try:
        with BaseScraper() as scraper:
            print("[DEBUG] Opening site...")
            scraper.goto("https://clays.bar/", timeout=60000, wait_until="domcontentloaded")
            scraper.wait_for_timeout(3000)

            # ---------------------------
            # ACCEPT COOKIES
            # ---------------------------
            try:
                print("[DEBUG] Clicking Accept Cookies...")
                scraper.click('button[aria-label="Accept All"]', timeout=3000)
            except:
                print("[DEBUG] No cookie popup shown.")

            scraper.wait_for_timeout(1500)

            # ---------------------------
            # GET SEARCH BAR SECTIONS
            # ---------------------------
            sections = scraper.page.locator(
                "//button[contains(@class,'SearchBarDesktop__Section-sc-1kwt1gr-2')]"
            ).all()

            print("[DEBUG] Found search bar sections:", len(sections))

            # -----------------------------------------------
            # LOCATION SECTION
            # -----------------------------------------------
            print("\n--- LOCATION SECTION ---")
            sections[0].evaluate("el => el.click()")
            scraper.wait_for_timeout(2000)

            loc_btn = scraper.page.locator(
                f"//span[contains(text(),'{location}')]"
            ).last

            print("[DEBUG] Clicking location")
            loc_btn.evaluate("el => el.click()")
            scraper.wait_for_timeout(1500)

            # -----------------------------------------------
            # DATE SECTION
            # -----------------------------------------------
            print("\n--- DATE SECTION ---")
            sections[1].evaluate("el => el.click()")
            scraper.wait_for_timeout(800)

            # ---- ENSURE CALENDAR OPEN ----
            def ensure_calendar_open():
                for i in range(10):
                    opened = scraper.page.evaluate("""() =>
                        document.querySelector('.react-calendar') !== null
                    """)
                    print(f"[DEBUG] ensure_calendar_open attempt {i+1}: {opened}")
                    if opened:
                        return True
                    sections[1].evaluate("el => el.click()")
                    scraper.wait_for_timeout(300)
                return False

            if not ensure_calendar_open():
                print("[ERROR] Calendar did not open.")
                return results

            # ---- GET MONTH HEADER ----
            def get_header():
                return scraper.page.evaluate("""() => {
                    let h = document.querySelector('.react-calendar__navigation__label span span');
                    return h ? h.textContent.trim() : null;
                }""")

            header = None
            for i in range(10):
                header = get_header()
                print(f"[DEBUG] header attempt {i+1}: {header}")
                if header:
                    break
                scraper.wait_for_timeout(250)

            if not header:
                raise Exception("Calendar header missing.")

            print(f"[DEBUG] Calendar showing: {header}")

            # ---- MOVE TO TARGET MONTH ----
            while header != target_month_year:
                print(f"[DEBUG] Navigating month → current: {header}")
                scraper.page.evaluate("""() => {
                    let n = document.querySelector('.react-calendar__navigation__next-button');
                    if (n) n.click();
                }""")
                scraper.wait_for_timeout(500)
                header = get_header()

            print(f"[DEBUG] Calendar at correct month: {header}")

            # -----------------------------------------
            # CLICK TARGET DATE BY TILE TEXT (PLAYWRIGHT SAFE)
            # -----------------------------------------
            target_day_text = day_num  # example "20"

            print(f"[DEBUG] Attempting tile-text click for day {target_day_text}")

            clicked = scraper.page.evaluate(f"""
                () => {{
                    const tiles = Array.from(document.querySelectorAll('button.react-calendar__tile'));

                    for (const tile of tiles) {{
                        const ab = tile.querySelector('abbr');
                        if (!ab) continue;

                        // Compare visible number text
                        if (ab.textContent.trim() === "{target_day_text}") {{
                            tile.dispatchEvent(new MouseEvent('click', {{
                                bubbles: true,
                                cancelable: true
                            }}));
                            return true;
                        }}
                    }}

                    return false;
                }}
            """)

            print("[DEBUG] tile-text click result:", clicked)
            scraper.wait_for_timeout(800)

            # -----------------------------------------
            # VERIFY SELECTION
            # -----------------------------------------
            active_date = scraper.page.evaluate("""
                () => {
                    let ab = document.querySelector('button.react-calendar__tile--active abbr');
                    return ab ? ab.textContent.trim() : null;
                }
            """)

            print("[DEBUG] Active date after click:", active_date)



            # -----------------------------------------------
            # TIME SELECTION (SAME AS SELENIUMBASE)
            # -----------------------------------------------
            print("\n--- TIME SECTION ---")

            try:
                dropdown = scraper.page.locator(
                    "select.WhenContent__TimeSelect-sc-5ndj3b-4"
                ).first

                dropdown.evaluate("""
                    el => {
                        el.selectedIndex = 1;
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                """)

                print("✔ Time selected")
            except Exception as e:
                print("❌ Time selection error:", e)

            scraper.wait_for_timeout(1500)

            # -----------------------------------------------
            # GUESTS (1 → target)
            # -----------------------------------------------
            print("\n--- GUESTS SECTION ---")

            sections[2].evaluate("el => el.click()")
            scraper.wait_for_timeout(800)

            # ensure popup visible
            for i in range(10):
                visible = scraper.page.evaluate("""
                    () => document.querySelector('input.WhoContent__CountInput-sc-fm3zg1-3') !== null
                """)
                print(f"[DEBUG] guest popup visible {i+1}: {visible}")
                if visible:
                    break
                sections[2].evaluate("el => el.click()")
                scraper.wait_for_timeout(300)

            # read current count
            current = scraper.page.evaluate("""
                () => {
                    let i = document.querySelector('input.WhoContent__CountInput-sc-fm3zg1-3');
                    return i ? parseInt(i.value) : 1;
                }
            """)

            print("[DEBUG] current guests:", current)

            dec = scraper.page.locator("button.decrement").first
            inc = scraper.page.locator("button.increment").first

            # reset to 1
            while current > 1:
                dec.evaluate("el => el.click()")
                current -= 1
                scraper.wait_for_timeout(150)

            # increase to target
            for _ in range(guests):
                inc.evaluate("el => el.click()")
                scraper.wait_for_timeout(150)

            print("✔ Guests set:", guests)

            scraper.page.evaluate("""
                () => {
                    let box = document.querySelector('.SearchBarDesktop__Container-sc-1kwt1gr-0');
                    if (box) box.click();
                }
            """)

            scraper.wait_for_timeout(1000)

            # -----------------------------------------------------------
            # OCCASION SECTION
            # -----------------------------------------------------------
            print("\n--- OCCASION SECTION ---")

            # Open the occasion dropdown
            sections[3].evaluate("el => el.click()")
            scraper.wait_for_timeout(600)

            # Ensure the popup stays open
            def ensure_occasion_open():
                for i in range(10):
                    exists = scraper.page.evaluate("""() =>
                        document.querySelectorAll('label.OccasionContent__RadioButtonContainer-sc-3wa38i-0').length > 0
                    """)
                    print(f"[DEBUG] occasion visible {i+1}: {exists}")
                    if exists:
                        return True
                    sections[3].evaluate("el => el.click()")
                    scraper.wait_for_timeout(400)
                return False

            if not ensure_occasion_open():
                print("[ERROR] Occasion popup not opening.")
            else:
                print("[DEBUG] Occasion options detected")

            # Select FIRST occasion (Birthday)
            success = scraper.page.evaluate("""
                () => {
                    let radios = document.querySelectorAll('label.OccasionContent__RadioButtonContainer-sc-3wa38i-0');
                    if (!radios.length) return false;

                    let evt = new MouseEvent('click', { bubbles: true, cancelable: true });
                    radios[0].dispatchEvent(evt);
                    return true;
                }
            """)

            print("[DEBUG] Occasion click success:", success)
            scraper.wait_for_timeout(500)


            # -----------------------------------------------
            # CLICK SEARCH
            # -----------------------------------------------
            print("\n--- SEARCH ---")
            scraper.page.evaluate("""
                () => {
                    let b = document.querySelector('button.SearchBarDesktop__SearchButton-sc-1kwt1gr-4');
                    if (b) b.click();
                }
            """)

            scraper.wait_for_timeout(7000)

            # -----------------------------------------------
            # PARSE RESULTS (NEW STRUCTURE)
            # -----------------------------------------------
            soup = BeautifulSoup(scraper.get_content(), "html.parser")

            print(f"[DEBUG] Searching for location: {location}")

            # 1. Find the place name div with Typography class containing the location
            # Look for divs with class containing "Typography__PoppinsLabel-sc-jdmbyi-1" and "bxlMrl"
            place_divs = soup.find_all("div", class_=lambda x: x and "Typography__PoppinsLabel-sc-jdmbyi-1" in x and "bxlMrl" in x)
            
            print(f"[DEBUG] Found {len(place_divs)} place name divs")
            
            # Find the div that contains our target location
            target_place_div = None
            for div in place_divs:
                place_text = div.get_text(strip=True)
                print(f"[DEBUG] Found place: {place_text}")
                # Check if location matches (case-insensitive, partial match)
                if location.lower() in place_text.lower() or place_text.lower() in location.lower():
                    target_place_div = div
                    print(f"[DEBUG] Matched location: {place_text}")
                    break
            
            if not target_place_div:
                print(f"[ERROR] Location '{location}' not found in place names!")
                # Log all available places for debugging
                for div in place_divs:
                    print(f"[DEBUG] Available place: {div.get_text(strip=True)}")
                return results

            # 2. Find the parent container that holds slots for this place
            # Navigate up the DOM to find the container with slots
            place_container = target_place_div
            for _ in range(10):  # Go up max 10 levels
                place_container = place_container.parent
                if place_container is None:
                    break
                # Look for slot-related elements in this container
                # Try to find time slots - they might be in buttons, divs, or spans
                potential_slots = place_container.find_all(["button", "div", "span"], 
                    class_=lambda x: x and ("time" in x.lower() or "slot" in x.lower() or "select" in x.lower()))
                if potential_slots:
                    print(f"[DEBUG] Found {len(potential_slots)} potential slot elements")
                    break

            # 3. Extract slots from the container
            # Look for various possible slot structures
            slot_elements = []
            
            # Try different selectors for slots
            selectors_to_try = [
                "button",  # Slots might be buttons
                "div[class*='Time']",  # Divs with Time in class
                "div[class*='Slot']",  # Divs with Slot in class
                "span[class*='Time']",  # Spans with Time in class
            ]
            
            for selector in selectors_to_try:
                found = place_container.select(selector) if place_container else []
                if found:
                    slot_elements = found
                    print(f"[DEBUG] Found {len(slot_elements)} slots using selector: {selector}")
                    break

            # If no slots found with specific selectors, try to find any clickable/time-related elements
            if not slot_elements and place_container:
                # Look for elements that might contain time information
                all_elements = place_container.find_all(["button", "div", "span"])
                # Filter for elements that might be slots (contain time-like text or have specific attributes)
                for elem in all_elements:
                    text = elem.get_text(strip=True)
                    # Check if it looks like a time slot (contains time pattern or price)
                    if text and (":" in text or "£" in text or "$" in text or "pm" in text.lower() or "am" in text.lower()):
                        slot_elements.append(elem)
                
                print(f"[DEBUG] Found {len(slot_elements)} slots by text pattern matching")

            if not slot_elements:
                print("[WARNING] No slot elements found. Trying alternative approach...")
                # Alternative: Look for the entire results section and parse all slots
                # Find all elements that might be slots on the page
                all_buttons = soup.find_all("button")
                all_divs = soup.find_all("div", class_=lambda x: x and ("time" in str(x).lower() or "slot" in str(x).lower()))
                
                # Get slots near the target place div
                if target_place_div:
                    # Find the section containing this place
                    section = target_place_div.find_parent("section") or target_place_div.find_parent("div")
                    if section:
                        slot_elements = section.find_all(["button", "div"], 
                            class_=lambda x: x and ("time" in str(x).lower() or "slot" in str(x).lower() or "select" in str(x).lower()))
                        print(f"[DEBUG] Found {len(slot_elements)} slots in section")

            print(f"[DEBUG] Total slots found: {len(slot_elements)}")

            # 4. Extract time and price from each slot
            for slot in slot_elements:
                slot_text = slot.get_text(strip=True)
                
                # Try to extract time (look for HH:MM pattern)
                time_match = re.search(r'(\d{1,2}:\d{2})', slot_text)
                time_val = time_match.group(1) if time_match else slot_text.split()[0] if slot_text else "None"
                
                # Try to extract price (look for £ or $)
                price_match = re.search(r'[£$]?(\d+(?:\.\d{2})?)', slot_text)
                price_val = price_match.group(0) if price_match else "None"
                
                # If no price found, use the full text as price/description
                if price_val == "None" and slot_text:
                    price_val = slot_text

                results.append({
                    "date": target_date,
                    "time": time_val,
                    "price": price_val,
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": venue_name
                })

            print(f"[DEBUG] Extracted {len(results)} slots for {location}")
            return results

    except Exception as e:
        print("[ERROR]", e)
        return results
