from flask import Flask, render_template, request, jsonify
import threading
from datetime import datetime
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
        print(holders, "@@@@")  # debug print

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

                # Time attribute
                try:
                    time = slot.select_one(
                        "div.es_booking__availability__table-cell"
                    )["name"]
                except:
                    time = "None"

                # Text inside time wrapper
                try:
                    desc = slot.select_one("div.es_booking__time_wrapper").get_text(strip=True)
                except:
                    desc = "None"

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

def scrape_lawn_club(guests, target_date, option="Curling Lawns & Cabins"):
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
        
        # Search for availability
        try:
            driver.click('button[data-test="sr-search-button"]')
            driver.sleep(4)
        except Exception as e:
            scraping_status['progress'] = 'Could not click search button'
            driver.quit()
            return
        
        scraping_status['progress'] = 'Searching for available slots on Lawn Club...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find('div','sc-huFNyZ cINeur').find_all('button')
        
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


def scrape_spin(guests, target_date):
    """SPIN NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        date_str = target_date
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)

        # Open reservation page
        driver.get(
            "https://wearespin.com/location/new-york-flatiron/table-reservations/"
            "#elementor-action%3Aaction%3Doff_canvas%3Aopen"
            "%26settings%3DeyJpZCI6ImM4OGU1Y2EiLCJkaXNwbGF5TW9kZSI6Im9wZW4ifQ%3D%3D"
        )
        
        scraping_status['progress'] = f'Navigating to SPIN NYC reservation system...'
        scraping_status['current_date'] = target_date
        
        # Click the booking button
        driver.click(
            'div.elementor-element.elementor-element-16e99e3.elementor-align-justify'
        )
        driver.sleep(3)

        # -----------------------------
        #   DETECT SevenRooms IFRAME
        # -----------------------------
        iframe = None

        for _ in range(60):  # wait up to 30 seconds
            iframes = driver.find_elements("css selector", "iframe")

            for f in iframes:
                src = f.get_attribute("src") or f.get_attribute("data-src")
                if src and "sevenrooms.com" in src:
                    iframe = f
                    break

            if iframe:
                break

            driver.sleep(0.5)

        if not iframe:
            scraping_status['progress'] = "SevenRooms iframe not found"
            driver.quit()
            return

        # -----------------------------
        #   FIX: correct Selenium syntax
        # -----------------------------
        driver.switch_to.frame(iframe)
        print("✔ Switched to SevenRooms iframe")

        scraping_status['progress'] = 'Accessing SPIN booking system...'
        
        # Wait for date buttons
        try:
            driver.wait_for_element('button[data-test="sr-calendar-date-button"]', timeout=30)
        except:
            scraping_status['progress'] = 'Page did not load properly for SPIN'
            driver.quit()
            return
        
        # -----------------------------
        #   Set the date
        # -----------------------------
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
        
        # -----------------------------
        #   Set guest count
        # -----------------------------
        while True:
            try:
                driver.click('button[aria-label="decrement Guests"]')
            except:
                break
        
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
        
        # -----------------------------
        #   Search availability
        # -----------------------------
        driver.click('button[data-test="sr-search-button"]')
        driver.sleep(4)
        
        scraping_status['progress'] = 'Searching for available slots on SPIN...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('button[data-test="sr-timeslot-button"]')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on SPIN'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on SPIN'
            driver.quit()
            return
        
        # -----------------------------
        #   Extract slots
        # -----------------------------
        for slot in slots:
            status = "Available"
            
            try:
                time = slot.find_all("div")[0].get_text().strip()
            except:
                time = "None"
                
            try:
                desc = slot.find_all("div")[1].get_text().strip()
            except:
                desc = "None"
            
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


def scrape_five_iron_golf(guests, target_date):
    """Five Iron Golf NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        date_str = target_date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%m/%d/%Y")
        
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        # Set 20-second page load timeout
        driver.set_page_load_timeout(20)

        
        try:
            driver.get("https://booking.fiveirongolf.com/session-length")
        except Exception:
            scraping_status["progress"] = "Page load timeout. Continuing..."
        
        scraping_status['progress'] = f'Navigating to Five Iron Golf NYC...'
        scraping_status['current_date'] = target_date
        
        try:
            driver.wait_for_element('div[role="combobox"][id="location-select"]', timeout=30)
        except Exception as e:
            scraping_status['progress'] = 'Page did not load properly for Five Iron Golf'
            driver.quit()
            return
        
        # Select location
        driver.click('div[role="combobox"][id="location-select"]')
        driver.sleep(3)
        driver.js_click('//li[normalize-space()="NYC - Flatiron"]')
        
        scraping_status['progress'] = f'Setting date to {target_date}...'
        
        # Set date
        date_input = driver.find_element("css selector", 'input[placeholder="mm/dd/yyyy"]')
        date_input.send_keys(Keys.CONTROL, "a")
        date_input.send_keys(Keys.DELETE)
        driver.type('input[placeholder="mm/dd/yyyy"]', formatted_date)
        
        # Set party size
        scraping_status['progress'] = f'Setting party size to {guests}...'
        # Price
        desc = "$70 per hour"
        if 7 <= int(guests) <= 12:
            guests = "7-12"
            # Price
            desc = "$140 per hour"
        elif int(guests) > 13:
            guests = "13+"
            
        driver.click('div[role="combobox"][id="party_size_select"]')
        driver.js_click(f'//li[normalize-space()="{guests}"]')
        
        driver.sleep(4)
        
        scraping_status['progress'] = 'Searching for available slots on Five Iron Golf...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('div.MuiToggleButtonGroup-root.css-9mqnp1')
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on Five Iron Golf'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on Five Iron Golf'
            driver.quit()
            return
        
        for slot in slots:
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.find_previous_sibling("h5").get_text().strip()
            except:
                time = "None"
                
            
            
            # Store data in memory
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


def scrape_clays_bar(location, guests, target_date):
    """Clays Bar (London) scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get("https://clays.bar/")
        
        scraping_status['progress'] = f'Navigating to Clays Bar {location}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)
        
        # Accept cookies
        try:
            accept = driver.find_element(
                "xpath",
                "//button[contains(@aria-label,'Accept All')]"
            )
            driver.execute_script("arguments[0].click();", accept)
        except:
            pass
        
        # Navigation through booking flow
        a_element = driver.find_elements(
            "xpath",
            "//button[contains(@class,'SearchBarDesktop__Section-sc-1kwt1gr-2 liVzmj')]"
        )
        
        # Location selection
        driver.execute_script("arguments[0].click();", a_element[0])
        driver.sleep(2)
        
        location_input = driver.find_elements(
            "xpath",
            f"//span[contains(text(),'{location}')]"
        )
        driver.execute_script("arguments[0].click();", location_input[-1])
        driver.sleep(2)
        
        # Date selection
        a_element[1].click()
        driver.sleep(3)
        
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        
        while True:
            try:
                date = driver.find_element(
                    "xpath",
                    f"//abbr[contains(@aria-label,'{str(formatted_date)}')]"
                )
                driver.execute_script("arguments[0].click();", date)
                
                # Time selection
                select_element = driver.find_element("xpath", "//select[contains(@class,'WhenContent__TimeSelect-sc-5ndj3b-4 geMVef')]")
                dropdown = Select(select_element)
                dropdown.select_by_visible_text("12:00pm")
                break
            except:
                try:
                    next_btn = driver.find_element(
                        "xpath",
                        "//button[contains(@class,'react-calendar__navigation__arrow react-calendar__navigation__next-button')]"
                    )
                    driver.execute_script("arguments[0].click();", next_btn)
                except:
                    print("couldn't click the next button")
                driver.sleep(2)
        
        # Guest count
        a_element[2].click()
        driver.type('input[class="WhoContent__CountInput-sc-fm3zg1-3 kiTuOv"]', str(guests))
        driver.sleep(2)
        
        # Occasion
        a_element[3].click()
        driver.sleep(2)
        
        occasion = driver.find_elements(
            "xpath",
            "//label[contains(text(),'No Occasion')]"
        )
        driver.execute_script("arguments[0].click();", occasion[0])
        
        # Search
        search = driver.find_elements(
            "xpath",
            "//button[contains(@class,'SearchBarDesktop__SearchButton-sc-1kwt1gr-4 cghPes')]"
        )
        driver.execute_script("arguments[0].click();", search[0])
        driver.sleep(10)
        
        scraping_status['progress'] = 'Searching for available slots on Clays Bar...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.select('div.TimeCarousel__Container-sc-vww6qk-1.cuGlzd')[0].select("div.TimeSlots__TimeStepWrapper-sc-1mnx04v-3.eCuxLB")
        
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
                time = slot.find("span",{"class":"TimeSelect__Time-sc-1usgwcy-1 gJDrjO"}).get_text().strip()
            except:
                time = "None"
                
            # Description/Price
            try:
                desc = slot.find("span",{"class":"TimeSelect__Price-sc-1usgwcy-2 dpRGEw"}).get_text().replace("\n","").strip()
            except:
                desc = "None"
            
            # Store data in memory
            slot_data = {
                'date': target_date,
                'time': time,
                'price': desc,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': f'Clays Bar ({location})'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([target_date, time, desc, status])
        
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


def scrape_f1_arcade(guests, target_date):
    """F1 Arcade (London) scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(uc=True, headless2=True, no_sandbox=True, disable_gpu=True)
        driver.get("https://f1arcade.com/uk/booking/venue/london")
        
        scraping_status['progress'] = f'Scraping F1 Arcade for {target_date}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)
        
        # Set guest count
        driver.type('input[id="adults-group-size"]', str(guests))
        
        continu = driver.find_elements("xpath", '//button[@id="game-continue"]')[1]
        driver.execute_script("arguments[0].click();", continu)
        
        # Date navigation
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        formatted = dt.strftime("%b %Y")
        day = dt.day
        
        driver.sleep(6)
        
        # Go back to start from earlier months
        for i in range(5):
            try:
                back = driver.find_element("xpath", '//button[@id="prev-month-btn"]')
                driver.execute_script("arguments[0].click();", back)
            except:
                pass
        
        # Navigate to target month
        while True:
            try:
                driver.assert_element(f"//h2[contains(text(),'{formatted}')]")
                break
            except:
                pass
            
            next_btn = driver.find_element("xpath", '//button[@id="next-month-btn"]')
            driver.execute_script("arguments[0].click();", next_btn)
        
        # Select day
        driver.js_click(f"//time[contains(text(),'{day}')]")
        
        try:
            driver.assert_element('//div[@data-target="time-picker-option"]', timeout=30)
        except:
            scraping_status['progress'] = 'No slots available on F1 Arcade'
            driver.quit()
            return
        
        scraping_status['progress'] = 'Searching for available slots on F1 Arcade...'
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all("div",{"data-target":"time-picker-option"})
        
        scraping_status['progress'] = f'Found {len(slots)} available slots on F1 Arcade'
        
        if len(slots) == 0:
            scraping_status['progress'] = 'No slots available on F1 Arcade'
            driver.quit()
            return
        
        for slot in slots:
            # Status
            status = "Available"
            
            # Time
            try:
                time = slot.get_text().strip()
            except:
                time = "None"
                
            # Description
            desc = "Peak from £24.95, Standard from £22.95"
            
            # Store data in memory
            slot_data = {
                'date': target_date,
                'time': time,
                'price': desc,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'website': 'F1 Arcade'
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
            
            print([target_date, time, desc, status])
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_restaurants(guests, target_date, website, lawn_club_option=None, clays_location=None, puttshack_location=None):
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
            scrape_lawn_club(guests, target_date, option)
        elif website == 'spin_nyc':
            if not target_date:
                raise ValueError("SPIN NYC requires a specific target date")
            scrape_spin(guests, target_date)
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
            scrape_f1_arcade(guests, target_date)
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
    return render_template('index.html')


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
    clays_location = data.get('clays_location')
    puttshack_location = data.get('puttshack_location')
    
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
    thread = threading.Thread(target=scrape_restaurants, args=(guests, target_date, website, lawn_club_option, clays_location, puttshack_location))
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
    app.run(debug=True, port=5005)
