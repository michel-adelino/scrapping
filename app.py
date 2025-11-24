from flask import Flask, render_template, request, jsonify
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from seleniumbase import Driver
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import re

app = Flask(__name__)


# Global variables to track scraping status and data
scraping_status = {
    'running': False,
    'progress': '',
    'completed': False,
    'error': None,
    'current_date': '',
    'total_slots_found': 0,
    'website': ''
}


# Store scraped data in memory
scraped_data = []


def _generate_lawn_club_time_options():
    """Build ordered list of valid Lawn Club time labels (15-min increments)."""
    times = []
    current = datetime.strptime("06:00 AM", "%I:%M %p")

    for _ in range(96):  # 6:00 AM through 5:45 AM next day
        label = current.strftime("%I:%M %p").lstrip("0")
        times.append(label)
        current += timedelta(minutes=15)

    return times


LAWN_CLUB_TIME_OPTIONS = _generate_lawn_club_time_options()
LAWN_CLUB_DURATION_OPTIONS = [
    "1 hr",
    "1 hr 30 min",
    "2 hr",
    "2 hr 30 min",
    "3 hr"
]


def normalize_time_value(raw_value):
    """Convert user-provided time to SevenRooms label format."""
    if not raw_value:
        return None
    cleaned = re.sub(r'\s+', ' ', raw_value.strip()).upper()
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]
    return cleaned


def normalize_duration_value(raw_value):
    """Normalize duration labels for comparison."""
    if not raw_value:
        return None
    return re.sub(r'\s+', ' ', raw_value.strip().lower())


def adjust_picker(driver, value_selector, increment_selector, decrement_selector, valid_values, target_value, normalize_fn=None):
    """Use picker arrows to land on requested value."""
    normalizer = normalize_fn or (lambda v: v)
    normalized_target = normalizer(target_value)

    normalized_values = [normalizer(val) for val in valid_values]
    if normalized_target not in normalized_values:
        raise ValueError(f"Unsupported value '{target_value}' for picker")
    
    max_attempts = len(valid_values) * 2
    for _ in range(max_attempts):
        temp = BeautifulSoup(driver.page_source, "html.parser")
        button = temp.select_one(value_selector)
        if not button:
            break
        
        value_container = button.find("div")
        current_value = value_container.get_text(strip=True) if value_container else None
        normalized_current = normalizer(current_value) if current_value else None

        if normalized_current == normalized_target:
            return True
        
        if normalized_current in normalized_values:
            current_idx = normalized_values.index(normalized_current)
            target_idx = normalized_values.index(normalized_target)
            click_selector = increment_selector if target_idx > current_idx else decrement_selector
        else:
            click_selector = increment_selector
        
        try:
            driver.click(click_selector)
        except Exception:
            pass
        
        driver.sleep(0.25)
    
    return False


def scrape_swingers(guests, target_date):
    """Original Swingers scraper function"""
    print ('guest--->>',guests)
    print ('target_date--->>',target_date)
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get(f"https://www.swingers.club/us/locations/nyc/book-now?guests={str(guests)}")
        
        scraping_status['progress'] = 'Starting to scrape Swingers availability...'
        
        while True:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            dates = soup.find_all("li",{"class":"slot-calendar__dates-item","data-available":"true"})
            
            scraping_status['progress'] = f'Found {len(dates)} available dates on Swingers'
            
            if len(dates) == 0:
                break
                
            for i in dates:
                date_str = i["data-date"]
                
                # If target_date is specified, only process that date
                if target_date and date_str != target_date:
                    continue
                
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                driver.get("https://www.swingers.club" + i.find("a")["href"])
                
                day = dt.strftime("%d")
                month = dt.strftime("%b")
                
                scraping_status['current_date'] = date_str
                scraping_status['progress'] = f'Processing Swingers slots for {date_str}'
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                slots = soup.find_all("button",{"data-day":day,"data-month":month})
                
                for slot in slots:
                    # Status
                    status_el = slot.select_one("div.slot-search-result__low-stock")
                    if status_el:
                        status = status_el.get_text(strip=True)
                    else:
                        status = "Available"
                    
                    # Time
                    try:
                        time = slot.find("span",{"class":"slot-search-result__time h5"}).get_text().strip()
                    except:
                        time = "None"
                    
                    # Price
                    try:
                        price = slot.find("span",{"class":"slot-search-result__price-label"}).get_text().strip()
                    except:
                        price = "None"
                    
                    # Store data in memory
                    slot_data = {
                        'date': date_str,
                        'time': time,
                        'price': price,
                        'status': status,
                        'timestamp': datetime.now().isoformat(),
                        'website': 'Swingers (NYC)'
                    }
                    
                    scraped_data.append(slot_data)
                    scraping_status['total_slots_found'] = len(scraped_data)
                    
                    print([date_str, time, price, status])
                
                # If target_date is specified, break after processing it
                if target_date and date_str == target_date:
                    break
            
            # If target_date is specified, don't click next
            if target_date:
                break
                
            driver.sleep(5)
            
            # Next button
            try:
                a_element = driver.find_element(
                    "xpath",
                    "//div[contains(@class,'slot-calendar__current-month-container')]/following::a[1]"
                )
                a_element.click()
                scraping_status['progress'] = 'Moving to next month on Swingers...'
            except:
                break
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_swingers_uk(guests, target_date):
    """Swingers UK scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get(f"https://www.swingers.club/uk/book-now?guests={str(guests)}")
        
        scraping_status['progress'] = 'Starting to scrape Swingers UK availability...'
        
        while True:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            dates = soup.find_all("li",{"class":"slot-calendar__dates-item","data-available":"true"})
            
            scraping_status['progress'] = f'Found {len(dates)} available dates on Swingers UK'
            
            if len(dates) == 0:
                break
                
            for i in dates:
                date_str = i["data-date"]
                
                # If target_date is specified, only process that date
                if target_date and date_str != target_date:
                    continue
                
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                driver.get("https://www.swingers.club" + i.find("a")["href"])
                
                day = dt.strftime("%d")
                month = dt.strftime("%b")
                
                scraping_status['current_date'] = date_str
                scraping_status['progress'] = f'Processing Swingers UK slots for {date_str}'
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                slots = soup.find_all("button",{"data-day":day,"data-month":month})
                
                for slot in slots:
                    # Status
                    status_el = slot.select_one("div.slot-search-result__low-stock")
                    if status_el:
                        status = status_el.get_text(strip=True)
                    else:
                        status = "Available"
                    
                    # Time
                    try:
                        time = slot.find("span",{"class":"slot-search-result__time h5"}).get_text().strip()
                    except:
                        time = "None"
                    
                    # Price
                    try:
                        price = slot.find("span",{"class":"slot-search-result__price-label"}).get_text().strip()
                    except:
                        price = "None"
                    
                    # Store data in memory
                    slot_data = {
                        'date': date_str,
                        'time': time,
                        'price': price,
                        'status': status,
                        'timestamp': datetime.now().isoformat(),
                        'website': 'Swingers (London)'
                    }
                    
                    scraped_data.append(slot_data)
                    scraping_status['total_slots_found'] = len(scraped_data)
                    
                    print([date_str, time, price, status])
                
                # If target_date is specified, break after processing it
                if target_date and date_str == target_date:
                    break
            
            # If target_date is specified, don't click next
            if target_date:
                break
                
            driver.sleep(5)
            
            # Next button
            try:
                a_element = driver.find_element(
                    "xpath",
                    "//div[contains(@class,'slot-calendar__current-month-container')]/following::a[1]"
                )
                driver.execute_script("arguments[0].click();", a_element)
                scraping_status['progress'] = 'Moving to next month on Swingers UK...'
            except:
                break
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_electric_shuffle(guests, target_date):
    """Electric Shuffle NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=False, no_sandbox=True, disable_gpu=True)
        driver.get(f"https://www.sevenrooms.com/explore/electricshufflenyc/reservations/create/search/?date={str(target_date)}&halo=120&party_size={str(guests)}&start_time=ALL")
        
        scraping_status['progress'] = f'Scraping Electric Shuffle NYC for {target_date}...'
        scraping_status['current_date'] = target_date
        
        try:
            driver.set_page_load_timeout(20)
            driver.wait_for_element('span[data-test="reservation-timeslot-button-description"]', timeout=15)
        except Exception as e:
            driver.set_page_load_timeout(20)
            scraping_status['progress'] = 'No slots available on Electric Shuffle NYC'
            driver.quit()
            return
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all('div','sc-imWYAI cTOWnZ')
        print(slots)
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Electric Shuffle NYC'
            driver.quit()
            return
        scraping_status['progress'] = f'Found {len(slots)} available slots on Electric Shuffle NYC'
        
        for slot in slots:
            date_str = target_date
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find('div').get_text().strip()
            except:
                time = "None"
                
            # Length (using as price equivalent)
            try:
                length = slot.get_text().strip()
            except:
                length = "None"
            
            # Store data in memory
            slot_data = {
                'date': date_str,
                'time': time,
                'price': length,  # Using length as price for consistency
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': 'Electric Shuffle (NYC)'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([date_str, time, length, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_electric_shuffle_london(guests, target_date):
    """Electric Shuffle London scraper function"""
    global scraping_status, scraped_data

    try:
        driver = Driver(
            uc=True,
            headless2=True,
            no_sandbox=True,
            disable_gpu=True
        )

        url = (
            f"https://electricshuffle.com/uk/london/book/shuffleboard?"
            f"preferedvenue=7&preferedtime=19%3A00&guestQuantity={guests}&date={target_date}"
        )

        driver.get(url)

        scraping_status['progress'] = f'Scraping Electric Shuffle London for {target_date}...'
        scraping_status['current_date'] = target_date

        # Let JS start loading
        driver.sleep(3)

        # ===============================
        #   WAIT UNTIL SLOTS FINISH LOADING
        # ===============================
        max_wait = 30
        interval = 0.5
        elapsed = 0

        while elapsed < max_wait:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            loading_div = soup.select_one(".es_booking__availability__message")
            slots_exist = soup.select_one("div.es_booking__availability__table-cell__wrapper")

            # CASE 1: slots are present
            if slots_exist:
                print("✔ Slots loaded")
                break

            # CASE 2: loading div text changed (means loading is done)
            if loading_div:
                text = loading_div.get_text(strip=True)
                if "Loading" not in text:
                    print("✔ Loading message disappeared")
                    break

            driver.sleep(interval)
            elapsed += interval

        if elapsed >= max_wait:
            scraping_status['progress'] = "Timeout: Slots did not load"
            driver.quit()
            return

        # ===============================
        #   PARSE THE PAGE AFTER LOADING
        # ===============================
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Form sections
        holders = soup.select("form.es_booking__availability__form")

        if not holders:
            scraping_status['progress'] = "No venue sections found on Electric Shuffle London"
            driver.quit()
            return

        scraping_status['progress'] = f"Found {len(holders)} venue sections on Electric Shuffle London"

        # Loop through each venue section
        for holder in holders:

            # Venue title
            try:
                holder_title = holder.select_one(
                    "div.es_booking__availability-header.es_font-body--semi-bold"
                ).get_text(strip=True)
            except:
                holder_title = "Unknown Venue"

            # Each slot row (wrapper)
            slots = holder.select("div.es_booking__availability__table-cell__wrapper")

            for slot in slots:
                date_str = target_date

                # extract time (radio button "name")
                try:
                    time = slot.select_one("div.es_booking__availability__table-cell")["name"]
                except:
                    time = "None"

                # ----------- Extract Time Wrapper -------------
                wrapper = slot.select_one("div.es_booking__time_wrapper")

                desc_parts = []

                if wrapper:
                    # Get all input elements inside wrapper (both disabled + enabled)
                    inputs = wrapper.select("input.es_booking__availability__time-slot")

                    for inp in inputs:
                        label = inp.find_next("label")

                        # Extract duration
                        dur_el = label.select_one(".es_booking__availability__duration")
                        duration = dur_el.get_text(strip=True) if dur_el else None
                        if duration:
                            duration = duration.replace("mins", "min").strip()

                        # Extract price
                        price_el = label.select_one(".es_booking__availability__price-per-person")
                        price_text = price_el.get_text(strip=True) if price_el else None

                        # CASE 1 — DISABLED SLOT
                        if inp.has_attr("disabled"):
                            desc_parts.append("unavailable")

                        # CASE 2 — ENABLED SLOT
                        else:
                            if duration and price_text:
                                desc_parts.append(f"{duration} {price_text}")
                            elif duration:
                                desc_parts.append(duration)
                            else:
                                desc_parts.append("available")
                                
                # Final text
                desc = ", ".join(desc_parts) if desc_parts else "unavailable"


                # wrapper = slot.select_one("div.es_booking__time_wrapper")

                # desc_parts = []

                # if wrapper:

                #     # Get all input elements inside wrapper (both disabled and enabled)
                #     inputs = wrapper.select("input.es_booking__availability__time-slot")

                #     for inp in inputs:
                #         label = inp.find_next("label")

                #         # Extract duration text
                #         dur_el = label.select_one(".es_booking__availability__duration")
                #         duration = dur_el.get_text(strip=True) if dur_el else None
                #         if duration:
                #             duration = duration.replace("mins", "min").replace("min", "min").strip()

                #         # Extract price text
                #         price_el = label.select_one(".es_booking__availability__price-per-person")
                #         price_pp = None
                #         if price_el:
                #             p = price_el.get_text(strip=True)
                #             p = p.replace("£", "").replace("pp", "").strip()
                #             try:
                #                 price_pp = float(p)
                #             except:
                #                 price_pp = None

                #         # CASE 1 — DISABLED → unavailable
                #         if inp.has_attr("disabled"):
                #             desc_parts.append("unavailable")

                #         # CASE 2 — ENABLED → duration + price
                #         else:
                #             if duration and price_pp:
                #                 total_price = price_pp * int(guests)
                #                 dollar_price = round(total_price * 1.66)
                #                 desc_parts.append(f"{duration} ${dollar_price}")

                # # Build final description
                # desc = ", ".join(desc_parts) if desc_parts else "unavailable"

                # ------------ Save Data ----------------------------
                slot_data = {
                    "date": date_str,
                    "time": time,
                    "price": f"{holder_title} - {desc}",
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": "Electric Shuffle (London)"
                }

                scraped_data.append(slot_data)
                scraping_status["total_slots_found"] = len(scraped_data)

                print([date_str, holder_title, time, desc, "Available"])

        driver.quit()

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e

def scrape_lawn_club(guests, target_date, option="Curling Lawns & Cabins", selected_time=None, selected_duration=None):
    """Lawn Club NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        date_str = target_date
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get("https://www.sevenrooms.com/landing/lawnclubnyc")
        
        scraping_status['progress'] = f'Navigating to Lawn Club NYC {option}...'
        
        driver.click(f'//a[contains(text(), "{option}")]')
        
        try:
            driver.wait_for_element('button[data-test="sr-calendar-date-button"]', timeout=30)
        except Exception as e:
            scraping_status['progress'] = 'Page did not load properly for Lawn Club'
            driver.quit()
            return
        
        scraping_status['progress'] = f'Setting date to {target_date} and guests to {guests}...'
        scraping_status['current_date'] = target_date
        
        # Navigate to the correct date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted = dt.strftime("%a, %b ") + str(dt.day)
        
        while True:
            temp = BeautifulSoup(driver.page_source, "html.parser")
            current_date_el = temp.find("button", {"data-test": "sr-calendar-date-button"})
            if not current_date_el:
                break
            current_date = current_date_el.find_all("div")[0].get_text()
            print(f"Current date: {current_date}, Target: {formatted}")
            if str(formatted) == current_date:
                break
            try:
                driver.click('button[aria-label="increment Date"]')
            except:
                break
        
        # Set guest count - first decrement to minimum
        while True:
            try:
                driver.click('button[aria-label="decrement Guests"]')
            except:
                break
        
        # Then increment to desired count
        while True:
            temp = BeautifulSoup(driver.page_source, "html.parser")
            guest_button = temp.find("button", {"data-test": "sr-guest-count-button"})
            if not guest_button:
                break
            current_guests = guest_button.find_all("div")[0].get_text().strip()
            if str(guests) == current_guests:
                break
            
            try:
                try:
                    driver.click('button[aria-label="increment Guests"]')
                except:
                    driver.click('button[aria-label="increment Guest"]')
            except:
                break
        
        normalized_time = normalize_time_value(selected_time)
        if normalized_time:
            scraping_status['progress'] = f'Selecting Lawn Club time {normalized_time}...'
            if not adjust_picker(
                driver,
                'button[data-test="sr-time-button"]',
                'button[aria-label="increment Time"]',
                'button[aria-label="decrement Time"]',
                LAWN_CLUB_TIME_OPTIONS,
                normalized_time,
                normalize_time_value
            ):
                raise RuntimeError(f"Could not set Lawn Club time to {normalized_time}")
            driver.sleep(0.3)
        
        normalized_duration = normalize_duration_value(selected_duration)
        if normalized_duration:
            scraping_status['progress'] = f'Selecting Lawn Club duration {normalized_duration}...'
            if not adjust_picker(
                driver,
                'button[data-test="sr-duration-picker"]',
                'button[aria-label="increment duration"]',
                'button[aria-label="decrement duration"]',
                LAWN_CLUB_DURATION_OPTIONS,
                normalized_duration,
                normalize_duration_value
            ):
                raise RuntimeError(f"Could not set Lawn Club duration to {normalized_duration}")
            driver.sleep(0.3)
        
        # Search for availability
        try:
            driver.click('button[data-test="sr-search-button"]')
            driver.sleep(4)
        except Exception as e:
            scraping_status['progress'] = 'Could not click search button'
            driver.quit()
            return
        
        scraping_status['progress'] = 'Searching for available slots on Lawn Club...'
        
        # Wait a bit more for results to load
        driver.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Try to find the slots container - handle case where it might not exist
        slots_container = soup.find('div', {'class': 'sc-huFNyZ cINeur'})
        if not slots_container:
            # Try alternative selectors
            slots_container = soup.find('div', class_=lambda x: x and 'sc-huFNyZ' in x)
            if not slots_container:
                # Try finding any container with time slots
                slots_container = soup.find('div', {'data-test': 'sr-time-slot-list'})
        
        if not slots_container:
            scraping_status['progress'] = 'No slots available on Lawn Club or page structure changed'
            driver.quit()
            return
        
        slots = slots_container.find_all('button')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Lawn Club'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Lawn Club'
            driver.quit()
            return
        
        for slot in slots:
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find_all("div")[0].get_text().strip()
            except:
                time = "None"
                
            # Description (using as price equivalent)
            try:
                desc = slot.find_all("div")[1].get_text().strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': date_str,
                'time': time,
                'price': desc,  # Using description as price for consistency
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': f'Lawn Club NYC ({option})'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([date_str, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


# def scrape_spin(guests, target_date):
#     """SPIN NYC scraper function"""
#     global scraping_status, scraped_data
    
#     try:
#         date_str = target_date
#         driver = Driver(uc=True, headless2=False, no_sandbox=True, disable_gpu=True)

#         # Open reservation page
#         driver.get(
#             "https://wearespin.com/location/new-york-flatiron/table-reservations/"
#             "#elementor-action%3Aaction%3Doff_canvas%3Aopen"
#             "%26settings%3DeyJpZCI6ImM4OGU1Y2EiLCJkaXNwbGF5TW9kZSI6Im9wZW4ifQ%3D%3D"
#         )
        
#         scraping_status['progress'] = f'Navigating to SPIN NYC reservation system...'
#         scraping_status['current_date'] = target_date
        
#         # Click the booking button
#         driver.click(
#             'div.elementor-element.elementor-element-16e99e3.elementor-align-justify'
#         )
#         driver.sleep(3)

#         # -----------------------------
#         #   DETECT SevenRooms IFRAME
#         # -----------------------------
#         iframe = None

#         for _ in range(60):  # wait up to 30 seconds
#             iframes = driver.find_elements("css selector", "iframe")

#             for f in iframes:
#                 src = f.get_attribute("src") or f.get_attribute("data-src")
#                 if src and "sevenrooms.com" in src:
#                     iframe = f
#                     break

#             if iframe:
#                 break

#             driver.sleep(0.5)

#         if not iframe:
#             scraping_status['progress'] = "SevenRooms iframe not found"
#             driver.quit()
#             return

#         # -----------------------------
#         #   FIX: correct Selenium syntax
#         # -----------------------------
#         driver.switch_to.frame(iframe)
#         print("✔ Switched to SevenRooms iframe")

#         scraping_status['progress'] = 'Accessing SPIN booking system...'
        
#         # Wait for date buttons
#         try:
#             driver.wait_for_element('button[data-test="sr-calendar-date-button"]', timeout=30)
#         except:
#             scraping_status['progress'] = 'Page did not load properly for SPIN'
#             driver.quit()
#             return
        
#         # -----------------------------
#         #   Set the date
#         # -----------------------------
#         dt = datetime.strptime(date_str, "%Y-%m-%d")
#         formatted = dt.strftime("%a, %b ") + str(dt.day)

#         scraping_status['progress'] = f'Setting date to {target_date}...'

#         while True:
#             temp = BeautifulSoup(driver.page_source, "html.parser")
#             current_date_button = temp.find("button", {"data-test": "sr-calendar-date-button"})
#             if not current_date_button:
#                 break

#             current_date = current_date_button.find_all("div")[0].get_text()

#             if str(formatted) == current_date:
#                 break
            
#             try:
#                 driver.click('button[aria-label="increment Date"]')
#             except:
#                 break
        
#         # -----------------------------
#         #   Set guest count
#         # -----------------------------
#         while True:
#             try:
#                 driver.click('button[aria-label="decrement Guests"]')
#             except:
#                 break
        
#         scraping_status['progress'] = f'Setting guests to {guests}...'
        
#         while True:
#             temp = BeautifulSoup(driver.page_source, "html.parser")
#             guest_button = temp.find("button", {"data-test": "sr-guest-count-button"})
#             if not guest_button:
#                 break

#             current_guests = guest_button.find_all("div")[0].get_text().strip()
            
#             if str(guests) == current_guests:
#                 break

#             try:
#                 try:
#                     driver.click('button[aria-label="increment Guests"]')
#                 except:
#                     driver.click('button[aria-label="increment Guest"]')
#             except:
#                 break
        
#         # -----------------------------
#         #   Search availability
#         # -----------------------------
#         driver.click('button[data-test="sr-search-button"]')
#         driver.sleep(4)
        
#         scraping_status['progress'] = 'Searching for available slots on SPIN...'
        
#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         slots = soup.select('button[data-test="sr-timeslot-button"]')
        
#         scraping_status['progress'] = f'Found {len(slots)} available slots on SPIN'
        
#         if len(slots) == 0:
#             scraping_status['progress'] = 'No slots available on SPIN'
#             driver.quit()
#             return
        
#         # -----------------------------
#         #   Extract slots
#         # -----------------------------
#         for slot in slots:
#             status = "Available"
            
#             try:
#                 time = slot.find_all("div")[0].get_text().strip()
#             except:
#                 time = "None"
                
#             try:
#                 desc = slot.find_all("div")[1].get_text().strip()
#             except:
#                 desc = "None"
            
#             slot_data = {
#                 'date': date_str,
#                 'time': time,
#                 'price': desc,
#                 'status': status,
#                 'timestamp': datetime.now().isoformat(),
#                 'website': 'SPIN (NYC)'
#             }
            
#             scraped_data.append(slot_data)
#             scraping_status['total_slots_found'] = len(scraped_data)
            
#             print([date_str, time, desc, status])
        
#         driver.quit()
        
#     except Exception as e:
#         if 'driver' in locals():
#             driver.quit()
#         raise e

def scrape_spin(guests, target_date, selected_time=None):
    """SPIN NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        date_str = target_date
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get("https://wearespin.com/location/new-york-flatiron/table-reservations/#elementor-action%3Aaction%3Doff_canvas%3Aopen%26settings%3DeyJpZCI6ImM4OGU1Y2EiLCJkaXNwbGF5TW9kZSI6Im9wZW4ifQ%3D%3D")
        
        scraping_status['progress'] = f'Navigating to SPIN NYC reservation system...'
        scraping_status['current_date'] = target_date
        
        driver.click('div[class="elementor-element elementor-element-16e99e3 elementor-align-justify elementor-widget elementor-widget-button"]')
        driver.sleep(4)
        
        iframe = driver.find_element("xpath", '//iframe[@nitro-lazy-src="https://www.sevenrooms.com/reservations/spinyc?duration-picker=false&defaultDuration=60"]')
        driver.switch_to.frame(iframe)
        
        scraping_status['progress'] = 'Accessing SPIN booking system...'
        
        try:
            driver.wait_for_element('button[data-test="sr-calendar-date-button"]', timeout=30)
        except Exception as e:
            scraping_status['progress'] = 'Page did not load properly for SPIN'
            driver.quit()
            return
        
        # Navigate to target date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted = dt.strftime("%a, %b ") + str(dt.day)
        
        scraping_status['progress'] = f'Setting date to {target_date}...'
        
        while True:
            temp = BeautifulSoup(driver.page_source, "html.parser")
            current_date_button = temp.find("button", {"data-test": "sr-calendar-date-button"})
            if not current_date_button:
                break
            current_date = current_date_button.find_all("div")[0].get_text()
            if str(formatted) == current_date:
                break
            try:
                driver.click('button[aria-label="increment Date"]')
            except:
                break
        
        # Set guest count - first decrement to minimum
        while True:
            try:
                driver.click('button[aria-label="decrement Guests"]')
            except:
                break
        
        # Then increment to desired count
        scraping_status['progress'] = f'Setting guests to {guests}...'
        
        while True:
            temp = BeautifulSoup(driver.page_source, "html.parser")
            guest_button = temp.find("button", {"data-test": "sr-guest-count-button"})
            if not guest_button:
                break
            current_guests = guest_button.find_all("div")[0].get_text().strip()
            if str(guests) == current_guests:
                break
            
            try:
                try:
                    driver.click('button[aria-label="increment Guests"]')
                except:
                    driver.click('button[aria-label="increment Guest"]')
            except:
                break
        
        normalized_time = normalize_time_value(selected_time)
        if normalized_time:
            scraping_status['progress'] = f'Selecting SPIN time {normalized_time}...'
            if not adjust_picker(
                driver,
                'button[data-test="sr-time-button"]',
                'button[aria-label="increment Time"]',
                'button[aria-label="decrement Time"]',
                LAWN_CLUB_TIME_OPTIONS,
                normalized_time,
                normalize_time_value
            ):
                raise RuntimeError(f"Could not set SPIN time to {normalized_time}")
            driver.sleep(0.3)
        
        # Search for availability
        driver.click('button[data-test="sr-search-button"]')
        driver.sleep(4)
        
        scraping_status['progress'] = 'Searching for available slots on SPIN...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('div.sc-huFNyZ.kQvFZy button[data-test="sr-timeslot-button"]')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on SPIN'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on SPIN'
            driver.quit()
            return
        
        for slot in slots:
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find_all("div")[0].get_text().strip()
            except:
                time = "None"
                
            # Description
            try:
                desc = slot.find_all("div")[1].get_text().strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': date_str,
                'time': time,
                'price': desc,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': 'SPIN (NYC)'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([date_str, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


# def scrape_five_iron_golf(guests, target_date):
#     """Five Iron Golf NYC scraper function"""
#     global scraping_status, scraped_data
    
#     try:
#         date_str = target_date
#         dt = datetime.strptime(date_str, "%Y-%m-%d")
#         formatted_date = dt.strftime("%m/%d/%Y")
        
#         driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
#         driver.set_page_load_timeout(20)

#         try:
#             driver.get("https://booking.fiveirongolf.com/session-length")
#         except Exception:
#             scraping_status["progress"] = "Page load timeout. Continuing..."
        
#         scraping_status['progress'] = f'Navigating to Five Iron Golf NYC...'
#         scraping_status['current_date'] = target_date
        
#         try:
#             driver.wait_for_element('div[role="combobox"][id="location-select"]', timeout=30)
#         except Exception:
#             scraping_status['progress'] = 'Page did not load properly for Five Iron Golf'
#             driver.quit()
#             return
        
#         # Select location
#         driver.click('div[role="combobox"][id="location-select"]')
#         driver.sleep(3)
#         driver.js_click('//li[normalize-space()="NYC - FiDi"]')
        
#         scraping_status['progress'] = f'Setting date to {target_date}...'
        
#         # Set date
#         date_input = driver.find_element("css selector", 'input[placeholder="mm/dd/yyyy"]')
#         date_input.send_keys(Keys.CONTROL, "a")
#         date_input.send_keys(Keys.DELETE)
#         driver.type('input[placeholder="mm/dd/yyyy"]', formatted_date)
        
#         # Set party size
#         scraping_status['progress'] = f'Setting party size to {guests}...'
        
#         driver.click('div[role="combobox"][id="party_size_select"]')
#         driver.js_click(f'//li[normalize-space()="{guests}"]')
        
#         driver.sleep(7)
        
#         scraping_status['progress'] = 'Searching for available slots on Five Iron Golf...'
        
#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         slots = soup.select('div.MuiToggleButtonGroup-root.css-9mqnp1')
        
#         scraping_status['progress'] = f'Found {len(slots)} available slots on Five Iron Golf'
        
#         if len(slots) == 0:
#             scraping_status['progress'] = 'No slots available on Five Iron Golf'
#             driver.quit()
#             return
        
#         for slot in slots:
#             status = "Available"
            
#             # Extract time
#             try:
#                 time = slot.find_previous_sibling("h5").get_text(strip=True)
#             except:
#                 time = "None"
            
#             # =============================
#             #   ✔ CORRECT PRICE EXTRACTION
#             # =============================
            
#             buttons = slot.select("button.MuiToggleButton-root")
#             price_parts = []
            
#             for btn in buttons:
#                 # duration ("1.5 hours", "2 hours")
#                 duration = btn.contents[0].strip()
                
#                 # price inside <p>
#                 price_el = btn.select_one("p")
#                 price = price_el.get_text(strip=True) if price_el else ""
                
#                 price_parts.append(f"{duration} {price}")
            
#             desc = ", ".join(price_parts)
            
#             # Store data
#             slot_data = {
#                 'date': date_str,
#                 'time': time,
#                 'price': desc,
#                 'status': status,
#                 'timestamp': datetime.now().isoformat(),
#                 'website': 'Five Iron Golf (NYC)'
#             }
            
#             scraped_data.append(slot_data)
#             scraping_status['total_slots_found'] = len(scraped_data)
            
#             print([date_str, time, desc, status])
        
#         driver.quit()
        
#     except Exception as e:
#         if 'driver' in locals():
#             driver.quit()
#         raise e


def scrape_five_iron_golf(guests, target_date):
    """Five Iron Golf NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        date_str = target_date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%m/%d/%Y")
        
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.set_page_load_timeout(20)

        try:
            driver.get("https://booking.fiveirongolf.com/session-length")
        except Exception:
            scraping_status["progress"] = "Page load timeout. Continuing..."
        
        scraping_status['progress'] = f'Navigating to Five Iron Golf NYC...'
        scraping_status['current_date'] = target_date
        
        try:
            driver.wait_for_element('div[role="combobox"][id="location-select"]', timeout=30)
        except Exception:
            scraping_status['progress'] = 'Page did not load properly for Five Iron Golf'
            driver.quit()
            return
        
        # Select location
        driver.click('div[role="combobox"][id="location-select"]')
        driver.sleep(3)
        driver.js_click('//li[normalize-space()="NYC - FiDi"]')
        
        scraping_status['progress'] = f'Setting date to {target_date}...'
        
        # Set date
        date_input = driver.find_element("css selector", 'input[placeholder="mm/dd/yyyy"]')
        date_input.send_keys(Keys.CONTROL, "a")
        date_input.send_keys(Keys.DELETE)
        driver.type('input[placeholder="mm/dd/yyyy"]', formatted_date)
        
        # Set party size
        scraping_status['progress'] = f'Setting party size to {guests}...'
        
        driver.click('div[role="combobox"][id="party_size_select"]')
        driver.js_click(f'//li[normalize-space()="{guests}"]')
        
        driver.sleep(7)
        
        scraping_status['progress'] = 'Searching for available slots on Five Iron Golf...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('div.MuiToggleButtonGroup-root.css-9mqnp1')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Five Iron Golf'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Five Iron Golf'
            driver.quit()
            return
        
        for slot in slots:
            status = "Available"
            
            # Extract time
            try:
                time = slot.find_previous_sibling("h5").get_text(strip=True)
            except:
                time = "None"
            
            # Extract each duration + price separately
            buttons = slot.select("button.MuiToggleButton-root")
            
            for btn in buttons:
                try:
                    duration = btn.contents[0].strip()      # "2 hours"
                except:
                    duration = "None"
                
                price_el = btn.select_one("p")
                price = price_el.get_text(strip=True) if price_el else ""

                # ❗ Skip rows where price is missing
                if not price:
                    continue

                # Convert "2 hours" → "2h"
                dur_clean = duration.replace(" hours", "h").replace(" hour", "h").strip()

                # Final format: "2h : $58"
                desc = f"{dur_clean} : {price}"

                slot_data = {
                    'date': date_str,
                    'time': time,
                    'price': desc,
                    'status': status,
                    'timestamp': datetime.now().isoformat(),
                    'website': 'Five Iron Golf (NYC)'
                }

                scraped_data.append(slot_data)
                scraping_status['total_slots_found'] = len(scraped_data)

                print([date_str, time, desc, status])


        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_lucky_strike(guests, target_date):
    """Lucky Strike NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        date_str = target_date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_str = str(int(dt.day) - 1)
        
        url = f"https://www.luckystrikeent.com/location/lucky-strike-chelsea-piers/booking/lane-reservation?date={target_date}T23:00:00.000Z&guestsCount={str(guests)}"
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get(url)
        
        scraping_status['progress'] = f'Navigating to Lucky Strike Chelsea Piers...'
        scraping_status['current_date'] = target_date
        
        try:
            driver.wait_for_element('button[class="TimeSlotSelection_timeSlot__hxKpB"]', timeout=30)
        except Exception as e:
            scraping_status['progress'] = 'No slots available on Lucky Strike'
            driver.quit()
            return
        
        if url != driver.current_url:
            scraping_status['progress'] = 'No dates available (redirected) on Lucky Strike'
            driver.quit()
            return
        
        scraping_status['progress'] = 'Searching for available slots on Lucky Strike...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('button.TimeSlotSelection_timeSlot__hxKpB')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Lucky Strike'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Lucky Strike'
            driver.quit()
            return
        
        for slot in slots:
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find_all("span")[0].get_text().strip()
            except:
                time = "None"
                
            # Description
            try:
                desc = slot.find_all("span")[1].get_text().strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': date_str,
                'time': time,
                'price': desc,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': 'Lucky Strike (NYC)'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([date_str, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_easybowl(guests, target_date):
    """Easybowl NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        # Convert date format from YYYY-MM-DD to DD-MM-YYYY
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        easybowl_date = dt.strftime("d-%d-%m-%Y")
        #
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get(f"https://www.easybowl.com/bc/LET/booking")
        
        scraping_status['progress'] = f'Scraping Easybowl NYC for {target_date}...'
        scraping_status['current_date'] = target_date
        while True:
            try:
                driver.click(f"td#{easybowl_date}")
                print('date found')
                break
            except:
                driver.click("//a[normalize-space()='>>']")
        
        select_element = driver.find_element("xpath", "//select[@id='adults']")
        dropdown = Select(select_element)

        dropdown.select_by_visible_text(str(guests))
        driver.click("//div[normalize-space()='Search']")
        driver.sleep(5)
        #
        selects = driver.find_elements("xpath", "//div[@class='button prodGroupButton']")
        
        for j in range(len(selects)):
            selects = driver.find_elements("xpath", "//div[@class='button prodGroupButton']")
            selects[j].click()
            driver.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Check if there's another layer of product groups (like PARTY PACKAGES)
            nested_groups = soup.find_all("div", {"class": "prodBox prodGroup"})
            
            if len(nested_groups) > 0:
                # This is a nested product group page (e.g., PARTY PACKAGES)
                # Need to click through each nested product group
                nested_selects = driver.find_elements("xpath", "//div[@class='button prodGroupButton']")
                
                for k in range(len(nested_selects)):
                    nested_selects = driver.find_elements("xpath", "//div[@class='button prodGroupButton']")
                    nested_selects[k].click()
                    driver.sleep(2)
                    
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    slots = soup.find_all("div", {"class": "prodBox"})
                    
                    # Filter out product groups (only get actual products)
                    actual_products = []
                    for slot in slots:
                        # Product groups have class "prodBox prodGroup", actual products just have "prodBox"
                        if "prodGroup" not in slot.get("class", []):
                            actual_products.append(slot)
                    
                    for slot in actual_products:
                        # Extract product name
                        name_el = slot.select_one("div.prodHeadline")
                        if name_el:
                            name = name_el.get_text(strip=True)
                        else:
                            name = "Unknown"
                        
                        # Extract time from event details
                        try:
                            event_table = slot.find("table", {"class": "tableEventDetails"})
                            if event_table:
                                time_rows = event_table.find_all("tr")
                                time_info = []
                                for row in time_rows:
                                    cells = row.find_all("td")
                                    if len(cells) >= 4:
                                        event_name = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                        start_time = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                        end_time = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                                        if start_time and end_time:
                                            time_info.append(f"{event_name}: {start_time} - {end_time}")
                                time = " | ".join(time_info) if time_info else event_table.get_text(strip=True)
                            else:
                                time = "None"
                        except:
                            time = "None"
                        
                        # Extract price
                        try:
                            price_table = slot.find("table", {"class": "tablePriceBox"})
                            if price_table:
                                price_rows = price_table.find_all("tr")
                                price_info = []
                                for row in price_rows:
                                    cells = row.find_all("td")
                                    if len(cells) >= 3:
                                        label = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                                        value = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                        if label and value:
                                            price_info.append(f"{label}: {value}")
                                price = " | ".join(price_info) if price_info else price_table.get_text(strip=True)
                            else:
                                price = "None"
                        except:
                            price = "None"
                        
                        # Store data in memory
                        slot_data = {
                            'date': target_date,
                            'time': time,
                            'price': price,
                            'status': name,
                            'timestamp': datetime.now().isoformat(),
                            'website': 'Easybowl (NYC)'
                        }
                        
                        scraped_data.append(slot_data)
                        scraping_status['total_slots_found'] = len(scraped_data)
                        
                        print([target_date, name, time, price])
                    
                    # Go back to nested product group page
                    driver.back()
                    driver.sleep(1)
            else:
                # Direct products page (no nested groups)
                slots = soup.find_all("div", {"class": "prodBox"})
                
                # Filter out product groups (only get actual products)
                actual_products = []
                for slot in slots:
                    # Product groups have class "prodBox prodGroup", actual products just have "prodBox"
                    if "prodGroup" not in slot.get("class", []):
                        actual_products.append(slot)
                
                for slot in actual_products:
                    # Extract product name
                    name_el = slot.select_one("div.prodHeadline")
                    if name_el:
                        name = name_el.get_text(strip=True)
                    else:
                        name = "Unknown"
                    
                    # Extract time from event details
                    try:
                        event_table = slot.find("table", {"class": "tableEventDetails"})
                        if event_table:
                            time_rows = event_table.find_all("tr")
                            time_info = []
                            for row in time_rows:
                                cells = row.find_all("td")
                                if len(cells) >= 4:
                                    event_name = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                    start_time = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                    end_time = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                                    if start_time and end_time:
                                        time_info.append(f"{event_name}: {start_time} - {end_time}")
                            time = " | ".join(time_info) if time_info else event_table.get_text(strip=True)
                        else:
                            time = "None"
                    except:
                        time = "None"
                    
                    # Extract price
                    try:
                        price_table = slot.find("table", {"class": "tablePriceBox"})
                        if price_table:
                            price_rows = price_table.find_all("tr")
                            price_info = []
                            for row in price_rows:
                                cells = row.find_all("td")
                                if len(cells) >= 3:
                                    label = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                                    value = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                    if label and value:
                                        price_info.append(f"{label}: {value}")
                            price = " | ".join(price_info) if price_info else price_table.get_text(strip=True)
                        else:
                            price = "None"
                    except:
                        price = "None"
                    
                    # Store data in memory
                    slot_data = {
                        'date': target_date,
                        'time': time,
                        'price': price,
                        'status': name,
                        'timestamp': datetime.now().isoformat(),
                        'website': 'Easybowl (NYC)'
                    }
                    
                    scraped_data.append(slot_data)
                    scraping_status['total_slots_found'] = len(scraped_data)
                    
                    print([target_date, name, time, price])
            
            # Reset to original page for next iteration
            driver.back()
            driver.sleep(1)
        scraping_status['progress'] = f'Found {len(scraped_data)} total slots on Easybowl'
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_fair_game_canary_wharf(guests, target_date):
    """Fair Game Canary Wharf (London) scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get(f"https://www.sevenrooms.com/explore/fairgame/reservations/create/search?date={target_date}&party_size={guests}")
        
        scraping_status['progress'] = f'Scraping Fair Game (Canary Wharf) for {target_date}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all("button", attrs={"data-test": re.compile("reservation-timeslot-button")})
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Fair Game (Canary Wharf)'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Fair Game (Canary Wharf)'
            driver.quit()
            return
        
        for slot in slots:
            date_str = target_date
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find("span",{"data-test":"reservation-timeslot-button-time"}).get_text().strip()
            except:
                time = "None"
                
            # Description
            try:
                desc = slot.find("span",{"data-test":"reservation-timeslot-button-description"}).get_text().replace("\n","").strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': date_str,
                'time': time,
                'price': desc,  # Using description as price for consistency
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': 'Fair Game (Canary Wharf)'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([date_str, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_fair_game_city(guests, target_date):
    """Fair Game City (London) scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get(f"https://www.sevenrooms.com/explore/fairgamecity/reservations/create/search/?date={target_date}&party_size={guests}")
        
        scraping_status['progress'] = f'Scraping Fair Game (City) for {target_date}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all("button", attrs={"data-test": re.compile("reservation-timeslot-button")})
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Fair Game (City)'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Fair Game (City)'
            driver.quit()
            return
        
        for slot in slots:
            date_str = target_date
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find("span",{"data-test":"reservation-timeslot-button-time"}).get_text().strip()
            except:
                time = "None"
                
            # Description
            try:
                desc = slot.find("span",{"data-test":"reservation-timeslot-button-description"}).get_text().replace("\n","").strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': date_str,
                'time': time,
                'price': desc,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': 'Fair Game (City)'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([date_str, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e



# def scrape_clays_bar(location, guests, target_date):
#     """Clays Bar (London) scraper function"""
#     global scraping_status, scraped_data

#     # Prepare date in a cross-platform safe way
#     date_obj = datetime.strptime(target_date, "%Y-%m-%d")

#     # Example: "November 2025"
#     target_month_year = date_obj.strftime("%B %Y")

#     # Example: "22 November 2025"
#     target_date_label = f"{date_obj.day} {date_obj.strftime('%B %Y')}"

#     # Example: "22" (works on all OS)
#     target_day = str(date_obj.day)

#     try:
#         driver = Driver(uc=True, headless2=False, no_sandbox=True, disable_gpu=True)
#         driver.get("https://clays.bar/")

#         scraping_status['progress'] = f'Navigating to Clays Bar {location}...'
#         scraping_status['current_date'] = target_date
        
        # driver.sleep(4)

        # # Accept cookies
        # try:
        #     driver.wait_for_element('button[aria-label="Accept All"]', timeout=10)
        #     driver.click('button[aria-label="Accept All"]')
        #     print("Clicked Accept All")
        # except Exception as e:
        #     print("Cookie accept error:", e)

#         # Click first search bar element (Where/When/Who/Occasion)
#         try:
#             a_element = driver.find_elements(
#                 "xpath",
#                 "//button[contains(@class,'SearchBarDesktop__Section-sc-1kwt1gr-2 liVzmj')]"
#             )
#             if a_element:
#                 print("✔ Search sections found → clicking first one")
#                 driver.execute_script("arguments[0].click();", a_element[0])
#                 # a_element[0].click()
#             else:
#                 print("⚠ No search bar section found")
#         except Exception as e:
#             print("Search bar click error:", e)

#         driver.sleep(5)

#         try:
#             # Select location
#             location_input = driver.find_elements(
#                 "xpath",
#                 f"//span[contains(text(),'{location}')]"
#             )
#             driver.execute_script("arguments[0].click();", location_input[-1])
#             driver.sleep(2)
#         except Exception as e:
#             print("error:",e)





def scrape_clays_bar(location, guests, target_date):
    """Clays Bar (London) scraper function"""
    global scraping_status, scraped_data

    # Prepare date in a cross-platform safe way
    date_obj = datetime.strptime(target_date, "%Y-%m-%d")

    # Example: "November 2025"
    target_month_year = date_obj.strftime("%B %Y")

    # Cross-platform day number
    try:
        day_num = date_obj.strftime("%-d")   # Linux / macOS
    except:
        day_num = date_obj.strftime("%#d")   # Windows

    # Correct aria-label format used by Clays Bar:
    # "November 25, 2025"
    target_date_label = f"{date_obj.strftime('%B')} {day_num}, {date_obj.year}"

    # Example: "25"
    target_day = day_num


    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get("https://clays.bar/")

        scraping_status['progress'] = f'Navigating to Clays Bar {location}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)

        # Accept cookies
        try:
            driver.wait_for_element('button[aria-label="Accept All"]', timeout=10)
            driver.click('button[aria-label="Accept All"]')
            print("Clicked Accept All")
        except Exception as e:
            print("Cookie accept error:", e)

        # Click search bar sections
        a_element = driver.find_elements(
            "xpath",
            "//button[contains(@class,'SearchBarDesktop__Section-sc-1kwt1gr-2')]"
        )
        driver.execute_script("arguments[0].click();", a_element[0])
        driver.sleep(3)

        # Select location
        location_input = driver.find_elements(
            "xpath",
            f"//span[contains(text(),'{location}')]"
        )
        driver.execute_script("arguments[0].click();", location_input[-1])
        driver.sleep(2)

        # -------------------------------------
        # 📅 OPEN DATE SECTION
        # -------------------------------------
        driver.execute_script("arguments[0].click();", a_element[1])
        driver.sleep(1)

        # -------------------------------------
        # 📅 FORCE THE CALENDAR TO STAY OPEN
        # -------------------------------------
        def ensure_calendar_open():
            for _ in range(5):
                cal = driver.execute_script("""
                    return document.querySelector('.react-calendar');
                """)
                if cal:
                    return True
                driver.execute_script("arguments[0].click();", a_element[1])
                driver.sleep(0.8)
            return False

        if not ensure_calendar_open():
            raise Exception("Calendar failed to stay open")


        # -------------------------------------
        # 📅 WAIT FOR HEADER
        # -------------------------------------
        def get_header():
            return driver.execute_script("""
                let h = document.querySelector('.react-calendar__navigation__label span span');
                return h ? h.textContent.trim() : null;
            """)

        header = None
        for _ in range(20):
            header = get_header()
            if header:
                break
            ensure_calendar_open()
            driver.sleep(0.3)

        if not header:
            raise Exception("Calendar header missing. Popup keeps closing.")


        # -------------------------------------
        # 📅 NAVIGATE MONTHS UNTIL TARGET
        # -------------------------------------
        while header != target_month_year:
            ensure_calendar_open()

            driver.execute_script("""
                let btn = document.querySelector('.react-calendar__navigation__next-button');
                if (btn) btn.click();
            """)

            driver.sleep(0.4)
            header = get_header()


        # -------------------------------------
        # 📅 CLICK THE TARGET DATE (JS CLICK)
        # -------------------------------------
        driver.execute_script(f"""
            let cells = document.querySelectorAll('abbr[aria-label="{target_date_label}"]');
            if (cells.length) cells[0].parentElement.click();
        """)
        driver.sleep(1)


        # -------------------------------------
        # 🕒 SELECT FIRST AVAILABLE TIME
        # -------------------------------------
        try:
            time_dropdown = driver.find_element(
                "css selector",
                "select.WhenContent__TimeSelect-sc-5ndj3b-4"
            )
            driver.execute_script("""
                let sel = arguments[0];
                sel.selectedIndex = 1;
                sel.dispatchEvent(new Event('change', { bubbles: true }));
            """, time_dropdown)
            print("✔ Time selected")
            driver.sleep(1)

        except Exception as e:
            print("❌ Time selection error:", e)


        # def ensure_who_open():
        #     """Force open the 'Who' popup until the guest input appears."""
        #     for _ in range(10):
        #         exists = driver.execute_script("""
        #             return document.querySelector('input.WhoContent__CountInput-sc-fm3zg1-3');
        #         """)
        #         if exists:
        #             return True

        #         # Click WHO section again
        #         try:
        #             driver.execute_script("arguments[0].click();", a_element[2])
        #         except:
        #             pass

        #         driver.sleep(0.5)
        #     return False



        # # -------------------------
        # # 👥 GUEST SELECTION (React-stable)
        # # -------------------------

        # # Step 1 — Ensure popup stays open
        # if not ensure_who_open():
        #     raise Exception("Who popup failed to stay open")

        # driver.sleep(0.5)

        # # Step 2 — Set value in React-controlled input
        # driver.execute_script("""
        #     let input = document.querySelector('input.WhoContent__CountInput-sc-fm3zg1-3');
        #     if (input) {
        #         input.value = arguments[0];
        #         input.dispatchEvent(new Event('input', { bubbles: true }));
        #         input.dispatchEvent(new Event('change', { bubbles: true }));
        #     }
        # """, str(guests))

        # driver.sleep(0.5)

        # # Step 3 — FORCE React to commit the changed value
        # # Click outside popup (on SearchBar container)
        # driver.execute_script("""
        #     let bar = document.querySelector('.SearchBarDesktop__Container-sc-1kwt1gr-0');
        #     if (bar) bar.click();
        # """)

        # driver.sleep(0.7)

        # print("✔ Guests saved permanently:", guests)


        def set_guests_value(guests):
            """Safely set the guest count using React increment/decrement buttons."""

            # Try to open WHO popup until visible
            for _ in range(10):
                popup_visible = driver.execute_script("""
                    return document.querySelector('input.WhoContent__CountInput-sc-fm3zg1-3');
                """)
                if popup_visible:
                    break
                # Open WHO section
                try:
                    driver.execute_script("arguments[0].click();", a_element[2])
                except:
                    pass
                driver.sleep(0.4)

            # Read current value
            current = driver.execute_script("""
                let inp = document.querySelector('input.WhoContent__CountInput-sc-fm3zg1-3');
                return inp ? parseInt(inp.value || "1") : null;
            """)

            if current is None:
                raise Exception("WHO popup not open")

            # Locate increment & decrement buttons
            decrement_btn = driver.find_element("css selector", "button.decrement")
            increment_btn = driver.find_element("css selector", "button.increment")

            # RESET guests to 1 first (React consistent)
            while current > 1:
                driver.execute_script("arguments[0].click();", decrement_btn)
                driver.sleep(0.12)
                current -= 1

            # INCREASE until target guests
            for _ in range(guests):
                driver.execute_script("arguments[0].click();", increment_btn)
                driver.sleep(0.12)

            # CLICK OUTSIDE to save React state
            driver.execute_script("""
                document.querySelector('.SearchBarDesktop__Container-sc-1kwt1gr-0')?.click();
            """)

            print("✔ Guests set successfully:", guests)
            driver.sleep(1)

        print("Selecting guests...")
        set_guests_value(guests)

        def ensure_occasion_open():
            """Force open the Occasion popup until radios appear."""
            for _ in range(10):
                exists = driver.execute_script("""
                    return document.querySelector('label.OccasionContent__RadioButtonContainer-sc-3wa38i-0');
                """)
                if exists:
                    return True

                try:
                    driver.execute_script("arguments[0].click();", a_element[3])
                except:
                    pass

                driver.sleep(0.6)

            return False

        # -------------------------
        # 🎉 OCCASION SELECTION (Stable)
        # -------------------------

        if not ensure_occasion_open():
            raise Exception("Occasion popup failed to stay open")

        # Select FIRST OCCASION using JS (Birthday)
        driver.execute_script("""
            let radios = document.querySelectorAll('label.OccasionContent__RadioButtonContainer-sc-3wa38i-0');
            if (radios.length > 0) {
                radios[0].click();
            }
        """)

        print("✔ Occasion selected (first option)")
        driver.sleep(1)

        # -------------------------
        # 🔍 CLICK SEARCH BUTTON (Stable)
        # -------------------------

        # Ensure search bar container is still present
        driver.sleep(1)

        try:
            # Query the search button directly
            search_btn = driver.find_element(
                "css selector",
                "button.SearchBarDesktop__SearchButton-sc-1kwt1gr-4"
            )

            driver.execute_script("arguments[0].click();", search_btn)
            print("✔ Search button clicked")

        except Exception as e:
            print("❌ Failed to click search button:", e)

        # Wait for results to load
        driver.sleep(5)

        # -------------------------------------
        # SCRAPE RESULTS
        # -------------------------------------
        soup = BeautifulSoup(driver.page_source, "html.parser")
        try:
            slots = soup.select(
                'div.TimeCarousel__Container-sc-vww6qk-1.cuGlzd'
            )[0].select(
                "div.TimeSlots__TimeStepWrapper-sc-1mnx04v-3.eCuxLB"
            )
        except:
            slots = []

        scraping_status['progress'] = f'Found {len(slots)} available slots on Clays Bar'

        if not slots:
            driver.quit()
            return

        for slot in slots:
            time_val = slot.find("span", {"class": "TimeSelect__Time-sc-1usgwcy-1 gJDrjO"})
            desc_val = slot.find("span", {"class": "TimeSelect__Price-sc-1usgwcy-2 dpRGEw"})

            time_val = time_val.get_text(strip=True) if time_val else "None"
            desc = desc_val.get_text(strip=True) if desc_val else "None"

            slot_data = {
                'date': target_date,
                'time': time_val,
                'price': desc,
                'status': "Available",
                'timestamp': datetime.now().isoformat(),
                'website': f'Clays Bar ({location})'
            }

            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            print([target_date, time_val, desc])

        driver.quit()

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e

        # ---------------------
        # 📅 DATE SELECTION FIXED
        # ---------------------

        # Click “When”
        driver.execute_script("arguments[0].click();", a_element[1])
        driver.sleep(5)

        # STEP 1 — Check if correct month already open
        try:
            header = driver.find_element(
                "xpath",
                "//button[contains(@class,'react-calendar__navigation__label')]//span"
            ).text.strip()

            if header == target_month_year:
                print("✔ Correct month visible:", header)
            else:
                raise Exception("Month does not match")
        except:
            print("⏳ Navigating calendar...")

            # STEP 2 — Navigate month-by-month
            while True:
                header = driver.find_element(
                    "xpath",
                    "//button[contains(@class,'react-calendar__navigation__label')]//span"
                ).text.strip()

                print("Current calendar:", header)

                if header == target_month_year:
                    print("✔ Month reached:", header)
                    break

                next_btn = driver.find_element(
                    "xpath",
                    "//button[contains(@class,'react-calendar__navigation__next-button')]"
                )
                driver.execute_script("arguments[0].click();", next_btn)
                driver.sleep(1)

        # STEP 3 — Click the correct date
        date_btn = driver.find_element(
            "xpath",
            f"//abbr[@aria-label='{target_date_label}']/parent::button"
        )
        driver.execute_script("arguments[0].click();", date_btn)
        print("✔ Date selected:", target_date_label)

        # Guest count
        a_element[2].click()
        driver.type('input[class="WhoContent__CountInput-sc-fm3zg1-3 kiTuOv"]', str(guests))
        driver.sleep(2)

        # Occasion
        a_element[3].click()
        driver.sleep(2)

        try:
            occasion_option = driver.find_element(
                "xpath",
                "//label[normalize-space()='No Occasion']"
            )
            driver.execute_script("arguments[0].click();", occasion_option)
            print("✔ Occasion selected")
        except Exception as e:
            print("❌ Failed to select occasion:", e)


        driver.sleep(10)

        scraping_status['progress'] = 'Searching for available slots on Clays Bar...'

        soup = BeautifulSoup(driver.page_source, "html.parser")
        try:
            slots = soup.select(
                'div.TimeCarousel__Container-sc-vww6qk-1.cuGlzd')[0].select(
                "div.TimeSlots__TimeStepWrapper-sc-1mnx04v-3.eCuxLB")
        except Exception as e:
            print("GGGGGGGG:",e)

        scraping_status['progress'] = f'Found {len(slots)} available slots on Clays Bar'

        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Clays Bar'
            driver.quit()
            return

        for slot in slots:
            # Status
            status = "Available"

            # Time
            try:
                time_val = slot.find("span", {"class": "TimeSelect__Time-sc-1usgwcy-1 gJDrjO"}).get_text().strip()
            except:
                time_val = "None"

            # Description/Price
            try:
                desc = slot.find("span", {"class": "TimeSelect__Price-sc-1usgwcy-2 dpRGEw"}).get_text().replace("\n","").strip()
            except:
                desc = "None"

            # Store data
            slot_data = {
                'date': target_date,
                'time': time_val,
                'price': desc,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': f'Clays Bar ({location})'
            }

            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)

            print([target_date, time_val, desc, status])

        driver.quit()

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_puttshack(location, guests, target_date):
    """Puttshack (London) scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get("https://www.puttshack.com/book-golf")
        
        scraping_status['progress'] = f'Navigating to Puttshack {location}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)
        
        # Country selection
        driver.click('button[class="input-button svelte-9udp5p"]')
        driver.click('div[data-label="United Kingdom"]')
        
        # Venue selection
        driver.click('button[aria-label="Venue Selector"]')
        
        a_element = driver.find_element(
            "xpath",
            f"//div[contains(text(),'{location}')]"
        )
        
        try:
            driver.execute_script("arguments[0].click();", a_element)
        except:
            pass
        
        # Date selection
        driver.click('button[aria-label="Date Selector"]')
        driver.sleep(10)
        
        # Navigate to correct month
        driver.click('button[aria-label="Previous"]')
        driver.click('button[aria-label="Previous"]')
        
        while True:
            try:
                driver.click(f'button[data-value="{target_date}"]')
                break
            except:
                try:
                    driver.click('button[aria-label="Next"]')
                except:
                    print("couldn't click the next button")
        
        # Player selection
        driver.click('button[aria-label="Player Selector"]')
        driver.sleep(2)
        
        while True:
            guests_holder = driver.find_elements(
                "xpath",
                "//div[contains(@class,'count svelte-1v5dv5l')]"
            )
            
            if guests_holder[0].text == str(guests):
                break
            else:
                try:
                    add = driver.find_elements(
                        "xpath",
                        "//button[contains(@aria-label,'Increase player count')]"
                    )
                    add[0].click()
                except:
                    print("couldn't click the add button")
        
        # Find time
        driver.click('button[aria-label="Find a time"]')
        driver.sleep(10)
        
        # Optional: choose session type
        try:
            choose = driver.find_elements(
                "xpath",
                "//button[contains(@data-ps-event,'click|handleRoute')]"
            )
            choose[0].click()
            driver.sleep(10)
        except:
            pass
        
        scraping_status['progress'] = 'Searching for available slots on Puttshack...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('button.timeslot.svelte-1ihytzt')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Puttshack'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Puttshack'
            driver.quit()
            return
        
        for slot in slots:
            # Check if disabled
            clss = slot.get("class")
            if "disabled" in clss:
                continue
            
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.get_text().strip()
            except:
                time = "None"
                
            # Description
            try:
                desc = slot.find("span",{"class":"adults svelte-1ihytzt"}).get_text().replace("\n","").strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': target_date,
                'time': time,
                'price': desc,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': f'Puttshack ({location})'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([target_date, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_flight_club_darts(guests, target_date, venue_id="1"):
    """Flight Club Darts (London) scraper function with venue selection"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get(f"https://flightclubdarts.com/book?date={target_date}&group_size={guests}&preferedtime=11%3A30&preferedvenue={venue_id}")
        
        # Determine venue name based on venue_id
        venue_names = {
            "1": "Flight Club Darts",
            "2": "Flight Club Darts (Angel)",
            "3": "Flight Club Darts (Shoreditch)",
            "4": "Flight Club Darts (Victoria)"
        }
        venue_name = venue_names.get(venue_id, "Flight Club Darts")
        
        scraping_status['progress'] = f'Scraping {venue_name} for {target_date}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        holders = soup.select('div.fc_dmnbook-availability')
        
        if len(holders) == 0:
            scraping_status['progress'] = f'No slots available on {venue_name}'
            driver.quit()
            return
        
        scraping_status['progress'] = f'Found {len(holders)} venue sections on {venue_name}'
        
        for holder in holders:
            try:
                holder_title = holder.find("span",{"id":"fc_dmnbook-availability__name"}).get_text().strip()
            except:
                holder_title = "Unknown Venue"
                
            slots = holder.find_all("div",{"class":"fc_dmnbook-availability-tablecell tns-item"})
            
            for slot in slots:
                date_str = target_date
                # Status
                status = "Available"
                
                # Time
                try:
                    time = slot.find("div",{"class":"fc_dmnbook-availibility__time font-small"}).get_text().strip()
                except:
                    time = "None"
                    
                # Description
                try:
                    desc = slot.find("div",{"class":"fc_dmnbook-time_wrapper"}).get_text().replace("\n","").strip()
                except:
                    desc = "None"
                
                # Store data in memory
                slot_data = {
                    'date': date_str,
                    'time': time,
                    'price': f"{holder_title} - {desc}",
                    'status': status,
                    'timestamp': datetime.now().isoformat(),
                    'website': venue_name
                }
                
                scraped_data.append(slot_data)
                scraping_status['total_slots_found'] = len(scraped_data)
                
                print([date_str, holder_title, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_f1_arcade(guests, target_date, f1_experience):
    """F1 Arcade (London) scraper with correct click order"""
    global scraping_status, scraped_data

    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get("https://f1arcade.com/uk/booking/venue/london")

        driver.sleep(4)

        # ----------------------------------------
        # 1️⃣ SET GUEST COUNT
        # ----------------------------------------
        scraping_status['progress'] = "Setting driver count..."
        size_box = driver.find_element("id", "adults-group-size")
        size_box.clear()
        size_box.send_keys(str(guests))

        driver.sleep(1)

        # ----------------------------------------
        # 2️⃣ SELECT EXPERIENCE (based on frontend)
        # ----------------------------------------
        scraping_status['progress'] = f"Selecting experience: {f1_experience}"

        experience_xpath = {
            "Team Racing": "//h2[contains(text(),'Team Racing')]",
            "Christmas Racing": "//h2[contains(text(),'Christmas Racing')]",
            "Head to Head": "//h2[contains(text(),'Head to Head')]"
        }

        xp = experience_xpath.get(f1_experience)

        if xp:
            try:
                exp_el = driver.find_element("xpath", xp)
                driver.execute_script("arguments[0].scrollIntoView(true);", exp_el)
                driver.sleep(1)
                driver.execute_script("arguments[0].click();", exp_el)
            except:
                print('not clicked')
                scraping_status['progress'] = f"Could not click {f1_experience}"
        else:
            scraping_status['progress'] = f"No matching experience for: {f1_experience}"

        driver.sleep(2)

        # ----------------------------------------
        # 3️⃣ CLICK CONTINUE after experience
        # ----------------------------------------
        scraping_status['progress'] = "Clicking Continue..."
        try:
            continue_btn = driver.find_element("id", "game-continue")
            driver.execute_script("arguments[0].click();", continue_btn)
        except:
            scraping_status['progress'] = "Continue button not found!"
            driver.quit()
            return

        driver.sleep(4)

        # ----------------------------------------
        # 4️⃣ CALENDAR – SELECT DATE
        # ----------------------------------------
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        target_month = dt.strftime("%b %Y")
        day = str(dt.day)

        scraping_status['progress'] = f"Finding month {target_month}..."

        # Reset calendar back a few months
        for _ in range(6):
            try:
                back = driver.find_element("id", "prev-month-btn")
                if back.is_enabled():
                    driver.execute_script("arguments[0].click();", back)
                    driver.sleep(0.3)
            except:
                break

        # Move forward until target month appears
        while True:
            header = driver.find_element("xpath", "//div[@id='date-picker']//h2").text.strip()
            if header == target_month:
                break
            next_btn = driver.find_element("id", "next-month-btn")
            driver.execute_script("arguments[0].click();", next_btn)
            driver.sleep(0.4)

        # Select the day
        scraping_status['progress'] = f"Selecting day {day}..."
        buttons = driver.find_elements("xpath", "//button[@data-target='date-picker-day']")

        day_clicked = False
        for btn in buttons:
            try:
                t = btn.find_element("tag name", "time").text.strip()
                if t == day and btn.is_enabled():
                    driver.execute_script("arguments[0].click();", btn)
                    day_clicked = True
                    break
            except:
                pass

        if not day_clicked:
            scraping_status['progress'] = f"Day {day} is not available"
            driver.quit()
            return

        driver.sleep(5)

        # ----------------------------------------
        # 5️⃣ READ TIME SLOTS
        # ----------------------------------------
        scraping_status['progress'] = "Fetching available times..."

        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all("div", {"data-target": "time-picker-option"})

        if not slots:
            scraping_status['progress'] = "No slots available"
            driver.quit()
            return

        for slot in slots:
            time_text = slot.get_text(strip=True)

            slot_data = {
                "date": target_date,
                "time": time_text,
                "price": "Peak from £24.95, Standard from £22.95",
                "status": "Available",
                "timestamp": datetime.now().isoformat(),
                "website": "F1 Arcade"
            }

            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)

        driver.quit()

    except Exception as e:
        if "driver" in locals():
            driver.quit()
        raise e

def scrape_restaurants(guests, target_date, website, lawn_club_option=None, lawn_club_time=None, lawn_club_duration=None, spin_time=None, clays_location=None, puttshack_location=None, f1_experience=None):
    """Main scraper function that calls appropriate scraper based on website"""
    global scraping_status, scraped_data
    
    try:
        scraping_status['running'] = True
        scraping_status['progress'] = 'Initializing browser...'
        scraping_status['completed'] = False
        scraping_status['error'] = None
        scraping_status['total_slots_found'] = 0
        scraping_status['website'] = website
        
        # Clear previous data
        scraped_data = []
        
        if website == 'swingers_nyc':
            scrape_swingers(guests, target_date)
        elif website == 'swingers_london':
            scrape_swingers_uk(guests, target_date)
        elif website == 'electric_shuffle_nyc':
            if not target_date:
                raise ValueError("Electric Shuffle NYC requires a specific target date")
            scrape_electric_shuffle(guests, target_date)
        elif website == 'electric_shuffle_london':
            if not target_date:
                raise ValueError("Electric Shuffle London requires a specific target date")
            scrape_electric_shuffle_london(guests, target_date)
        elif website == 'lawn_club_nyc':
            if not target_date:
                raise ValueError("Lawn Club NYC requires a specific target date")
            option = lawn_club_option or "Curling Lawns & Cabins"
            scrape_lawn_club(guests, target_date, option, lawn_club_time, lawn_club_duration)
        elif website == 'spin_nyc':
            if not target_date:
                raise ValueError("SPIN NYC requires a specific target date")
            scrape_spin(guests, target_date, spin_time)
        elif website == 'five_iron_golf_nyc':
            if not target_date:
                raise ValueError("Five Iron Golf NYC requires a specific target date")
            scrape_five_iron_golf(guests, target_date)
        elif website == 'lucky_strike_nyc':
            if not target_date:
                raise ValueError("Lucky Strike NYC requires a specific target date")
            scrape_lucky_strike(guests, target_date)
        elif website == 'easybowl_nyc':
            if not target_date:
                raise ValueError("Easybowl NYC requires a specific target date")
            scrape_easybowl(guests, target_date)
        elif website == 'fair_game_canary_wharf':
            if not target_date:
                raise ValueError("Fair Game (Canary Wharf) requires a specific target date")
            scrape_fair_game_canary_wharf(guests, target_date)
        elif website == 'fair_game_city':
            if not target_date:
                raise ValueError("Fair Game (City) requires a specific target date")
            scrape_fair_game_city(guests, target_date)
        elif website == 'clays_bar':
            if not target_date:
                raise ValueError("Clays Bar requires a specific target date")
            location = clays_location or "Canary Wharf"
            scrape_clays_bar(location, guests, target_date)
        elif website == 'puttshack':
            if not target_date:
                raise ValueError("Puttshack requires a specific target date")
            location = puttshack_location or "Bank"
            scrape_puttshack(location, guests, target_date)
        elif website == 'flight_club_darts':
            if not target_date:
                raise ValueError("Flight Club Darts requires a specific target date")
            scrape_flight_club_darts(guests, target_date, "1")
        elif website == 'flight_club_darts_angel':
            if not target_date:
                raise ValueError("Flight Club Darts (Angel) requires a specific target date")
            scrape_flight_club_darts(guests, target_date, "2")
        elif website == 'flight_club_darts_shoreditch':
            if not target_date:
                raise ValueError("Flight Club Darts (Shoreditch) requires a specific target date")
            scrape_flight_club_darts(guests, target_date, "3")
        elif website == 'flight_club_darts_victoria':
            if not target_date:
                raise ValueError("Flight Club Darts (Victoria) requires a specific target date")
            scrape_flight_club_darts(guests, target_date, "4")
        elif website == 'f1_arcade':
            if not target_date:
                raise ValueError("F1 Arcade requires a specific target date")
            experience = f1_experience or "Team Racing"
            scrape_f1_arcade(guests, target_date, experience)
        else:
            raise ValueError(f"Unknown website: {website}")
        
        scraping_status['running'] = False
        scraping_status['completed'] = True
        scraping_status['progress'] = f'Scraping completed! Found {len(scraped_data)} total slots on {website.replace("_", " ").title()}'
        
    except Exception as e:
        scraping_status['running'] = False
        scraping_status['error'] = str(e)
        scraping_status['progress'] = f'Error: {str(e)}'


@app.route('/')
def index():
    return render_template(
        'index.html',
        lawn_club_times=LAWN_CLUB_TIME_OPTIONS,
        lawn_club_durations=LAWN_CLUB_DURATION_OPTIONS
    )


@app.route('/run_scraper', methods=['POST'])
def run_scraper():
    global scraping_status
    
    if scraping_status['running']:
        return jsonify({'error': 'Scraper is already running'}), 400
    
    data = request.get_json()
    guests = data.get('guests')
    target_date = data.get('target_date')
    website = data.get('website', 'swingers_nyc')  # Default to swingers NYC
    lawn_club_option = data.get('lawn_club_option')
    lawn_club_time = data.get('lawn_club_time')
    lawn_club_duration = data.get('lawn_club_duration')
    spin_time = data.get('spin_time')
    clays_location = data.get('clays_location')
    puttshack_location = data.get('puttshack_location')
    f1_experience = data.get("f1_experience")
 
    # Validate and normalize target_date format (YYYY-MM-DD) to avoid timezone issues
    if target_date:
        try:
            # Validate date format
            datetime.strptime(target_date, "%Y-%m-%d")
            # Ensure it's in the correct format (no time component)
            if 'T' in target_date or ' ' in target_date:
                target_date = target_date.split('T')[0].split(' ')[0]
            print(f"Received target_date: {target_date}")
        except ValueError:
            return jsonify({'error': f'Invalid date format: {target_date}. Expected YYYY-MM-DD'}), 400
    
    if not guests:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    required_date_websites = [
        'electric_shuffle_nyc', 'electric_shuffle_london', 'lawn_club_nyc', 'spin_nyc', 
        'five_iron_golf_nyc', 'lucky_strike_nyc', 'easybowl_nyc',
        'fair_game_canary_wharf', 'fair_game_city', 'clays_bar', 'puttshack', 
        'flight_club_darts', 'flight_club_darts_angel', 'flight_club_darts_shoreditch', 
        'flight_club_darts_victoria', 'f1_arcade'
    ]
    
    if website in required_date_websites and not target_date:
        website_names = {
            'electric_shuffle_nyc': 'Electric Shuffle NYC',
            'electric_shuffle_london': 'Electric Shuffle London',
            'lawn_club_nyc': 'Lawn Club NYC',
            'spin_nyc': 'SPIN NYC',
            'five_iron_golf_nyc': 'Five Iron Golf NYC',
            'lucky_strike_nyc': 'Lucky Strike NYC',
            'easybowl_nyc': 'Easybowl NYC',
            'fair_game_canary_wharf': 'Fair Game (Canary Wharf)',
            'fair_game_city': 'Fair Game (City)',
            'clays_bar': 'Clays Bar',
            'puttshack': 'Puttshack',
            'flight_club_darts': 'Flight Club Darts',
            'flight_club_darts_angel': 'Flight Club Darts (Angel)',
            'flight_club_darts_shoreditch': 'Flight Club Darts (Shoreditch)',
            'flight_club_darts_victoria': 'Flight Club Darts (Victoria)',
            'f1_arcade': 'F1 Arcade'
        }
        return jsonify({'error': f'{website_names[website]} requires a specific target date'}), 400
    
    # Start scraping in a separate thread
    thread = threading.Thread(target=scrape_restaurants, args=(guests, target_date, website, lawn_club_option, lawn_club_time, lawn_club_duration, spin_time, clays_location, puttshack_location, f1_experience))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started successfully'})


@app.route('/status')
def get_status():
    return jsonify(scraping_status)


@app.route('/data')
def get_data():
    """Get scraped data"""
    return jsonify({
        'data': scraped_data,
        'total_count': len(scraped_data)
    })


@app.route('/clear_data', methods=['POST'])
def clear_data():
    """Clear scraped data"""
    global scraped_data
    scraped_data = []
    return jsonify({'message': 'Data cleared successfully'})


if __name__ == '__main__':
    app.run(debug=True,port=8000)
