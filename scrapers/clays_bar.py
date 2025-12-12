"""Clays Bar scraper using Playwright (FULLY FIXED VERSION)"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

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
            # PARSE RESULTS (TARGET DATE ONLY)
            # -----------------------------------------------
            soup = BeautifulSoup(scraper.get_content(), "html.parser")

            # Build label → e.g. "Sat, Dec 20"
            try:
                day_label = date_obj.strftime("%a, %b %-d")  # linux
            except:
                day_label = date_obj.strftime("%a, %b %#d")  # windows

            print(f"[DEBUG] Searching for day block: {day_label}")

            # 1. Find the correct day container
            day_block = None
            for block in soup.select("div.TimeStep__Day-sc-qa67fz-5"):
                label_el = block.select_one("span.TimeStep__DayLabel-sc-qa67fz-6")
                if label_el and label_el.get_text(strip=True) == day_label:
                    day_block = block
                    break

            if not day_block:
                print("[ERROR] Target day block NOT found!")
                return results

            print("[DEBUG] Found correct day block")

            # 2. Extract slots ONLY inside this block
            slot_wrappers = day_block.select(
                "div.TimeSlots__TimeStepWrapper-sc-1mnx04v-3"
            )

            print(f"[DEBUG] Found {len(slot_wrappers)} slot wrappers for {day_label}")

            for slot in slot_wrappers:
                time_el = slot.find("span", class_="TimeSelect__Time-sc-1usgwcy-1")
                price_el = slot.find("span", class_="TimeSelect__Price-sc-1usgwcy-2")

                results.append({
                    "date": target_date,
                    "time": time_el.get_text(strip=True) if time_el else "None",
                    "price": price_el.get_text(strip=True) if price_el else "None",
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": venue_name
                })

            return results

    except Exception as e:
        print("[ERROR]", e)
        return results
