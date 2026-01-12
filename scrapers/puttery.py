import requests
import json
import time
import os
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

logger = logging.getLogger(__name__)

class ExploretockAutomation:
    def __init__(self, guest_count=3, desired_date="12/23/2025", headless=True, flaresolverr_url=None):
        """
        Hybrid approach: FlareSolverr for Cloudflare bypass + Selenium for interactions

        Prerequisites:
        - FlareSolverr running: docker run -d -p 8191:8191 flaresolverr/flaresolverr
        - Chrome/Chromium installed
        """
        self.website_url = "https://www.exploretock.com/puttery-new-york/"
        self.guest_count = guest_count
        self.desired_date = desired_date
        # Use provided URL or environment variable, default to localhost
        self.flaresolverr_url = flaresolverr_url or os.getenv('FLARESOLVERR_URL', 'http://localhost:8191/v1')
        self.session_id = None
        self.cookies = []
        self.user_agent = None
        self.headless = headless
        self.driver = None
        self.wait = None
        self.max_retries = 3
        self.original_date_format = None  # Store original date format for return

    def log(self, message, status="INFO"):
        """Print formatted log messages"""
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✓",
            "ERROR": "✗",
            "STEP": "📍",
            "START": "🚀",
            "WARNING": "⚠️",
            "DEBUG": "🔍"
        }
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")

    def create_flaresolverr_session(self):
        """Create FlareSolverr session and bypass Cloudflare"""
        payload = {
            "cmd": "request.get",
            "url": self.website_url,
            "maxTimeout": 60000
        }

        try:
            self.log("Requesting page through FlareSolverr...", "INFO")
            response = requests.post(self.flaresolverr_url, json=payload, timeout=90)
            result = response.json()

            if result.get("status") == "ok" and result.get("solution"):
                solution = result["solution"]
                self.cookies = solution.get("cookies", [])
                self.user_agent = solution.get("userAgent", "")
                self.log("FlareSolverr bypass successful", "SUCCESS")
                self.log(f"Retrieved {len(self.cookies)} cookies", "INFO")
                return True

            self.log(f"FlareSolverr failed: {result.get('message', 'Unknown error')}", "ERROR")
            return False

        except requests.exceptions.ConnectionError:
            self.log("Cannot connect to FlareSolverr on port 8191", "ERROR")
            self.log("Start it with: docker run -d -p 8191:8191 flaresolverr/flaresolverr", "INFO")
            return False
        except Exception as e:
            self.log(f"FlareSolverr error: {e}", "ERROR")
            return False

    def init_selenium_with_cookies(self):
        """Initialize Selenium browser with cookies from FlareSolverr"""
        try:
            self.log("Initializing Selenium with FlareSolverr cookies...", "INFO")

            options = Options()
            options.binary_location = '/usr/bin/google-chrome-stable'
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")

            if self.user_agent:
                options.add_argument(f"user-agent={self.user_agent}")

            if self.headless:
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-gpu")
            else:
                options.add_argument("--start-maximized")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 25)

            # Navigate to domain first (required to set cookies)
            self.log("Loading domain to inject cookies...", "INFO")
            self.driver.get(self.website_url)
            time.sleep(2)

            # Inject cookies from FlareSolverr
            if self.cookies:
                for cookie in self.cookies:
                    try:
                        # Selenium cookie format
                        cookie_dict = {
                            'name': cookie.get('name'),
                            'value': cookie.get('value'),
                            'domain': cookie.get('domain'),
                            'path': cookie.get('path', '/'),
                        }
                        if 'expiry' in cookie:
                            cookie_dict['expiry'] = cookie['expiry']
                        if 'secure' in cookie:
                            cookie_dict['secure'] = cookie['secure']
                        if 'httpOnly' in cookie:
                            cookie_dict['httpOnly'] = cookie['httpOnly']

                        self.driver.add_cookie(cookie_dict)
                    except Exception as e:
                        self.log(f"Failed to add cookie {cookie.get('name')}: {e}", "DEBUG")

                self.log(f"Injected {len(self.cookies)} cookies into browser", "SUCCESS")

            # Refresh page with cookies
            self.log("Reloading page with injected cookies...", "INFO")
            self.driver.refresh()
            time.sleep(3)

            return True

        except Exception as e:
            self.log(f"Failed to initialize Selenium: {e}", "ERROR")
            return False
    def delay_ms(self, ms):
        """Delay in milliseconds"""
        time.sleep(ms / 1000)

    def scroll_to_element(self, element):
        """Scroll element into view"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.delay_ms(500)
        except:
            pass

    def click_element_js(self, selector, description, by=By.CSS_SELECTOR):
        """Click element using JavaScript"""
        for attempt in range(self.max_retries):
            try:
                element = self.wait.until(EC.presence_of_element_located((by, selector)))
                self.scroll_to_element(element)
                self.driver.execute_script("arguments[0].click();", element)
                self.log(f"Clicked: {description}", "SUCCESS")
                self.delay_ms(1000)
                return True
            except Exception as e:
                if attempt == self.max_retries - 1:
                    self.log(f"Failed to click {description}: {str(e)}", "ERROR")
                    return False
                self.log(f"Retrying {description}...", "INFO")
                time.sleep(1.5)
        return False

    def wait_for_modal_open(self):
        """Wait for modal dialog to open"""
        try:
            self.log("Waiting for modal dialog to open...", "INFO")

            modal_selectors = [
                '[id*="experience-dialog"]',
                '[role="dialog"]',
                '.MuiDialog-root'
            ]

            modal_found = False
            for selector in modal_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                    self.log(f"Modal found with selector: {selector}", "INFO")
                    modal_found = True
                    break
                except:
                    continue

            if modal_found:
                self.delay_ms(3000)
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="guest-selector-text"]')))
                    self.delay_ms(2000)
                except:
                    pass
                self.log("Modal fully loaded", "SUCCESS")
                return True
            else:
                self.log("Modal not found, continuing anyway...", "WARNING")
                self.delay_ms(5000)
                return True

        except Exception as e:
            self.log(f"Error waiting for modal: {str(e)}", "WARNING")
            self.delay_ms(5000)
            return True

    def get_modal_guest_count(self):
        """Get current guest count from modal"""
        try:
            selector_text = None
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, '.SearchBarModalContainer')
                selector_text = container.find_element(By.CSS_SELECTOR, '[data-testid="guest-selector-text"]')
            except:
                try:
                    selector_text = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="guest-selector-text"]')
                except:
                    return None

            if selector_text:
                text = selector_text.text
                match = re.search(r'(\d+)\s+guests', text)
                if match:
                    return int(match.group(1))
        except:
            pass
        return None

    def set_modal_guest_count(self, target_count):
        """Set guest count in modal"""
        try:
            self.log("Finding guest selector...", "INFO")

            guest_selector = None
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, '.SearchBarModalContainer')
                guest_selector = container.find_element(By.CSS_SELECTOR, '[data-testid="guest-selector"]')
            except:
                try:
                    guest_selector = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="guest-selector"]')
                except:
                    self.log("Could not find guest selector", "ERROR")
                    return False

            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="guest-selector-text"]')))
            self.delay_ms(1500)

            current_count = self.get_modal_guest_count()
            if current_count is None:
                self.log("Could not get guest count", "ERROR")
                return False

            self.log(f"Current: {current_count}, Target: {target_count}", "INFO")

            if current_count == target_count:
                self.log(f"Guest count already set to {target_count}", "SUCCESS")
                return True

            try:
                plus_btn = guest_selector.find_element(By.CSS_SELECTOR, '[data-testid="guest-selector_plus"]')
                minus_btn = guest_selector.find_element(By.CSS_SELECTOR, '[data-testid="guest-selector_minus"]')
            except:
                self.log("Could not find plus/minus buttons", "ERROR")
                return False

            if current_count < target_count and plus_btn.get_attribute("disabled"):
                self.log(f"Cannot increase to {target_count}. Max capacity reached.", "ERROR")
                return False

            iterations = 0
            max_iterations = 20

            while self.get_modal_guest_count() != target_count and iterations < max_iterations:
                current = self.get_modal_guest_count()

                if current < target_count:
                    if not plus_btn.get_attribute("disabled"):
                        self.scroll_to_element(plus_btn)
                        self.driver.execute_script("arguments[0].click();", plus_btn)
                        self.delay_ms(700)
                    else:
                        self.log(f"Cannot reach {target_count}", "ERROR")
                        return False
                elif current > target_count:
                    self.scroll_to_element(minus_btn)
                    self.driver.execute_script("arguments[0].click();", minus_btn)
                    self.delay_ms(700)

                iterations += 1

            final_count = self.get_modal_guest_count()
            if final_count == target_count:
                self.log(f"Guest count set to {target_count}", "SUCCESS")
                return True
            else:
                self.log(f"Failed to set guest count. Final: {final_count}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error setting guest count: {str(e)}", "ERROR")
            return False

    def select_modal_date(self, date_str):
        """Select date in modal calendar"""
        try:
            self.log(f"Selecting date {date_str}...", "INFO")

            day = date_str.split('/')[1].lstrip('0')
            self.log(f"Looking for day {day} in calendar...", "INFO")

            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ConsumerCalendar')))
            self.delay_ms(1500)

            date_found = False
            for attempt in range(4):
                try:
                    first_calendar = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="calendar-first"]')
                    all_day_buttons = first_calendar.find_elements(By.CSS_SELECTOR, 'button.ConsumerCalendar-day')

                    self.log(f"Found {len(all_day_buttons)} day buttons", "INFO")

                    for btn in all_day_buttons:
                        try:
                            day_text = btn.find_element(By.CSS_SELECTOR, 'span').text.strip()

                            if day_text == day:
                                btn_classes = btn.get_attribute('class')
                                is_disabled = 'is-disabled' in btn_classes or btn.get_attribute('disabled')

                                if not is_disabled and 'is-in-month' in btn_classes:
                                    self.log(f"Clicking date {day}...", "SUCCESS")
                                    self.scroll_to_element(btn)
                                    self.delay_ms(500)
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    self.delay_ms(2500)
                                    date_found = True
                                    break
                        except:
                            continue

                    if date_found:
                        break

                    self.delay_ms(800)

                except Exception as e:
                    self.delay_ms(800)
                    continue

            if date_found:
                self.log(f"Date selected: {date_str}", "SUCCESS")
                self.delay_ms(4000)
                return True
            else:
                self.log(f"Failed to select date {date_str}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error selecting date: {str(e)}", "ERROR")
            return False

    def scrape_modal_times(self):
        """Scrape available times from modal"""
        times = []
        try:
            self.log("Waiting for time slots to load...", "INFO")
            self.delay_ms(3000)

            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="search-result"]')))
            self.delay_ms(2000)

            time_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="search-result"]')
            self.log(f"Found {len(time_elements)} time slots", "INFO")

            for idx, element in enumerate(time_elements):
                try:
                    time_elem = element.find_element(By.CSS_SELECTOR, '[data-testid="search-result-time"]')
                    time_text = time_elem.text.strip()

                    try:
                        availability_elem = element.find_element(By.CSS_SELECTOR, '[data-testid="communal-count-text"]')
                        availability_text = availability_elem.text.strip()
                    except:
                        availability_text = "Available"

                    if time_text and time_text not in ['-', '']:
                        # Generate booking URL with date and size parameters
                        booking_url = (
                            f"https://www.exploretock.com/puttery-new-york/experience/556314/play-1-course-reservation-weekday"
                            f"?date={self.original_date_format}&size={self.guest_count}"
                        )
                        
                        # Return format expected by the app
                        times.append({
                            "date": self.original_date_format,  # YYYY-MM-DD format
                            "time": time_text,
                            "price": availability_text or "Available",
                            "status": "Available",
                            "website": "Puttery (NYC)",
                            "booking_url": booking_url
                        })

                except Exception as e:
                    continue

            self.log(f"Successfully scraped {len(times)} time slots", "SUCCESS")
            return times

        except Exception as e:
            self.log(f"Error scraping times: {str(e)}", "ERROR")
            return []

    def print_available_times(self, times):
        """Print times in formatted table"""
        if not times:
            self.log("No available times to display", "ERROR")
            return

        print("\n" + "=" * 60)
        print(f"AVAILABLE TIME SLOTS FOR {self.desired_date}")
        print("=" * 60)
        print(f"{'#':<4} {'TIME':<15} {'AVAILABILITY':<30}")
        print("-" * 60)
        for i, slot in enumerate(times, 1):
            print(f"{i:<4} {slot['time']:<15} {slot['availability']:<30}")
        print("=" * 60 + "\n")

    def run(self):
        """Main automation flow"""
        try:
            self.log("Starting Exploretock Automation (FlareSolverr + Selenium)", "START")

            # Step 1: Bypass Cloudflare with FlareSolverr
            self.log("Step 1: Bypassing Cloudflare with FlareSolverr", "STEP")
            if not self.create_flaresolverr_session():
                self.log("Failed to bypass Cloudflare", "ERROR")
                return False

            # Step 2: Initialize Selenium with cookies
            self.log("Step 2: Initializing Selenium with cookies", "STEP")
            if not self.init_selenium_with_cookies():
                self.log("Failed to initialize Selenium", "ERROR")
                return False

            self.delay_ms(5000)

            # Step 3: Click reservation to open modal
            self.log("Step 3: Clicking reservation to open modal", "STEP")
            if not self.click_element_js(
                    '[data-testid="offering-link_Play1CourseReservationWeekday"]',
                    "First Reservation"
            ):
                self.log("Failed to click reservation", "ERROR")
                return False

            if not self.wait_for_modal_open():
                self.log("Modal did not open properly", "ERROR")
                return False

            self.delay_ms(3000)

            # Step 4: Set guest count
            self.log("Step 4: Setting guest count in modal", "STEP")
            if not self.set_modal_guest_count(self.guest_count):
                self.log("Failed to set guest count", "ERROR")
                return False

            self.delay_ms(1500)

            # Step 5: Select date
            self.log("Step 5: Selecting date in modal", "STEP")
            if not self.select_modal_date(self.desired_date):
                self.log("Failed to select date", "ERROR")
                return False

            self.delay_ms(2000)

            # Step 6: Scrape times
            self.log("Step 6: Scraping available times", "STEP")
            times = self.scrape_modal_times()

            if times:
                self.print_available_times(times)
                self.log("✅ Automation completed successfully!", "SUCCESS")
                return times
            else:
                self.log("No times found", "WARNING")
                return []

        except Exception as e:
            self.log(f"Unexpected error: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()
            return []

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass


def scrape_puttery(guests, target_date):
    """
    Scrape Puttery NYC availability
    
    Args:
        guests: Number of guests (integer)
        target_date: Date in YYYY-MM-DD format (string)
    
    Returns:
        List of availability slots with date, time, price, status
        Format: [{"date": "YYYY-MM-DD", "time": "HH:MM", "price": "...", "status": "Available", "website": "Puttery (NYC)"}, ...]
    """
    results = []
    
    try:
        logger.info(f"[PUTTERY] Starting scrape for {guests} guests on {target_date}")
        
        # Convert date format from YYYY-MM-DD to MM/DD/YYYY
        date_parts = target_date.split('-')
        if len(date_parts) != 3:
            logger.error(f"[PUTTERY] Invalid date format: {target_date}. Expected YYYY-MM-DD")
            return results
        
        formatted_date = f"{date_parts[1]}/{date_parts[2]}/{date_parts[0]}"  # MM/DD/YYYY
        
        # Get FlareSolverr URL from environment variable
        flaresolverr_url = os.getenv('FLARESOLVERR_URL', 'http://localhost:8191/v1')
        logger.info(f"[PUTTERY] Using FlareSolverr URL: {flaresolverr_url}")
        
        # Create automation instance
        automation = ExploretockAutomation(
            guest_count=guests,
            desired_date=formatted_date,
            headless=True,
            flaresolverr_url=flaresolverr_url
        )
        automation.original_date_format = target_date  # Store original format for return
        
        # Run the automation - it returns the scraped times
        results = automation.run()
        
        if results:
            logger.info(f"[PUTTERY] Successfully scraped {len(results)} time slots")
        else:
            logger.warning(f"[PUTTERY] No time slots found")
        
        # Cleanup is handled in the finally block of run()
        if automation.driver:
            try:
                automation.driver.quit()
            except:
                pass
                
    except Exception as e:
        logger.error(f"[PUTTERY] Error during scraping: {e}", exc_info=True)
    
    return results


if __name__ == "__main__":
    print("=" * 80)
    print("EXPLORETOCK AUTOMATION - PUTTERY NEW YORK")
    print("=" * 80)
    print("\n⚠️  PREREQUISITES:")
    print("   1. FlareSolverr must be running on port 8191")
    print("      docker run -d -p 8191:8191 flaresolverr/flaresolverr")
    print("\n   2. Chrome/Chromium browser installed")
    print("   3. ChromeDriver compatible with your Chrome version")
    print("=" * 80 + "\n")

    # Configuration
    GUEST_COUNT = 3
    DESIRED_DATE = "12/23/2025"
    HEADLESS = True  # Set True for headless mode

    automation = ExploretockAutomation(
        guest_count=GUEST_COUNT,
        desired_date=DESIRED_DATE,
        headless=HEADLESS
    )
    automation.run()
