"""F1 Arcade scraper using Playwright"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


def scrape_f1_arcade(guests, target_date, f1_experience):
    """
    F1 Arcade scraper (Playwright version)
    Converted from your SeleniumBase logic
    """

    print("\n==================== F1 ARCADE (PLAYWRIGHT) ====================\n")
    print(f"[DEBUG] Guests: {guests}")
    print(f"[DEBUG] Date:   {target_date}")
    print(f"[DEBUG] XP:     {f1_experience}")

    results = []

    # --------------------------------------------------------------------
    # Experience map (converted directly from your Selenium XPaths)
    # --------------------------------------------------------------------
    xp_map = {
        "Team Racing": "//h2[contains(text(),'Team Racing')]",
        "Christmas Racing": "//h2[contains(text(),'Christmas Racing')]",
        "Head to Head": "//h2[contains(text(),'Head to Head')]"
    }

    xp_xpath = xp_map.get(f1_experience)

    try:
        with BaseScraper() as scraper:

            # Open home page
            scraper.goto("https://f1arcade.com/uk/booking/venue/london",
                         timeout=60000, wait_until="domcontentloaded")
            scraper.wait_for_timeout(4000)

            # -----------------------------------------------------------------
            # 1️⃣ SET GUEST COUNT
            # -----------------------------------------------------------------
            print("[DEBUG] Setting guest count...")

            scraper.page.evaluate(f"""
                () => {{
                    let el = document.getElementById("adults-group-size");
                    if (el) {{
                        el.value = "{guests}";
                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                    }}
                }}
            """)

            scraper.wait_for_timeout(800)

            # -----------------------------------------------------------------
            # 2️⃣ SELECT EXPERIENCE
            # -----------------------------------------------------------------
            if xp_xpath:
                print(f"[DEBUG] Selecting experience: {f1_experience}")

                xp_btn = scraper.page.locator(xp_xpath)
                if xp_btn.count() > 0:
                    xp_btn.first.evaluate("el => el.scrollIntoView()")
                    scraper.wait_for_timeout(600)
                    xp_btn.first.evaluate("el => el.click()")
                else:
                    print(f"[WARN] Experience not found: {f1_experience}")

            scraper.wait_for_timeout(1500)

            # -----------------------------------------------------------------
            # 3️⃣ CLICK CONTINUE
            # -----------------------------------------------------------------
            print("[DEBUG] Clicking Continue button")

            cont = scraper.page.locator("#game-continue")

            count = cont.count()
            print(f"[DEBUG] Continue buttons found: {count}")

            if count == 0:
                print("❌ Continue button missing, exiting")
                return results

            # Use the FIRST visible Continue button
            first_btn = cont.first

            # Scroll into view for safety
            first_btn.evaluate("el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
            scraper.wait_for_timeout(500)

            # JS click – avoids strict mode and overlay issues
            clicked = scraper.page.evaluate("""
                () => {
                    let btn = document.querySelector('#game-continue');
                    if (btn) { btn.click(); return true; }
                    return false;
                }
            """)

            print("[DEBUG] Continue clicked:", clicked)
            scraper.wait_for_timeout(2000)


            scraper.wait_for_timeout(4000)

            # -----------------------------------------------------------------
            # 4️⃣ CALENDAR LOGIC
            # -----------------------------------------------------------------
            dt = datetime.strptime(target_date, "%Y-%m-%d")
            target_month = dt.strftime("%b %Y")
            day = str(dt.day)

            print(f"[DEBUG] Target Month: {target_month}, Day: {day}")

            # Reset calendar backwards first
            for _ in range(6):
                scraper.page.evaluate("""
                    () => {
                        let b = document.getElementById("prev-month-btn");
                        if (b) b.click();
                    }
                """)
                scraper.wait_for_timeout(180)

            # Move forward to target month
            while True:
                header = scraper.page.evaluate("""
                    () => {
                        let h = document.querySelector('#date-picker h2');
                        return h ? h.textContent.trim() : "";
                    }
                """)
                if header == target_month:
                    break

                scraper.page.evaluate("""
                    () => {
                        let b = document.getElementById("next-month-btn");
                        if (b) b.click();
                    }
                """)

                scraper.wait_for_timeout(250)

            # Select day
            print("[DEBUG] Clicking day:", day)

            clicked = scraper.page.evaluate(f"""
                () => {{
                    let btns = document.querySelectorAll(
                        'button[data-target="date-picker-day"]'
                    );
                    for (let b of btns) {{
                        let t = b.querySelector("time");
                        if (!t) continue;
                        if (t.textContent.trim() === "{day}" && !b.disabled) {{
                            b.click();
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)

            if not clicked:
                print(f"❌ Day {day} unavailable")
                return results

            scraper.wait_for_timeout(8000)

            # -----------------------------------------------------------------
            # 5️⃣ PRICE HEADER PARSING
            # -----------------------------------------------------------------
            print("[DEBUG] Extracting price types...")

            soup = BeautifulSoup(scraper.get_content(), "html.parser")

            price_headers = soup.select(".flex.grow.justify-center")
            price_map = {}  # {"Offpeak": "19.95", "Standard": "22.95"}

            for block in price_headers:
                label_div = block.find("div", class_="-mt-1")
                if not label_div:
                    continue

                label = label_div.find("div").get_text(strip=True)
                price_div = label_div.find("div", class_="text-xxs")

                if price_div:
                    clean_price = price_div.get_text(strip=True).replace("from £", "")
                    price_map[label] = clean_price

            # -----------------------------------------------------------------
            # 6️⃣ COLOR → PRICE MAP
            # -----------------------------------------------------------------
            COLOR_PRICE_CLASS = {
                "bg-light-grey": "Offpeak",
                "bg-electric-violet-light": "Standard",
                "bg-brand-primary": "Peak"
            }

            # -----------------------------------------------------------------
            # 7️⃣ TIME SLOT EXTRACTION
            # -----------------------------------------------------------------
            print("[DEBUG] Extracting time slots...")

            slots = soup.find_all("div", {"data-target": "time-picker-option"})

            for slot in slots:
                time_text = slot.get_text(strip=True)

                inner = slot.find("div", class_="animate")
                if not inner:
                    continue

                box = inner.find("div")
                if not box:
                    continue

                classes = box.get("class", [])

                price_type = "Unknown"
                for c in classes:
                    if c in COLOR_PRICE_CLASS:
                        price_type = COLOR_PRICE_CLASS[c]
                        break

                final_price = f"{price_type} from £{price_map.get(price_type, 'N/A')}"

                results.append({
                    "date": target_date,
                    "time": time_text,
                    "price": final_price,
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": "F1 Arcade"
                })

            print(f"[DEBUG] Extracted {len(results)} slots")

            return results

    except Exception as e:
        print("[ERROR] F1 Arcade scraper crashed:", e)
        return results
