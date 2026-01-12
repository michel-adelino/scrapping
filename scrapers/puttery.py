import requests
import json
import time
import os
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.sync_api import Browser, BrowserContext, Page
import re
from browser_utils import create_browser, create_browser_context, create_page, create_browser_with_context
import logging

logger = logging.getLogger(__name__)

class ExploretockAutomation:
    def __init__(self, guest_count=3, desired_date="12/23/2025", headless=True, flaresolverr_url=None):
        """
        Hybrid approach: FlareSolverr for Cloudflare bypass + Playwright for interactions

        Prerequisites:
        - FlareSolverr running: docker run -d -p 8191:8191 flaresolverr/flaresolverr
        - Playwright browsers installed: playwright install chromium
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
        self.browser = None
        self.context = None
        self.page = None
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

    def init_playwright_with_cookies(self):
        """Initialize Playwright browser with cookies from FlareSolverr"""
        try:
            self.log("Initializing Playwright with FlareSolverr cookies...", "INFO")

            # Create browser with context
            browser_kwargs = {'headless': self.headless}
            if self.user_agent:
                browser_kwargs['user_agent'] = self.user_agent
            
            self.browser, self.context = create_browser_with_context(**browser_kwargs)
            
            # Create page
            self.page = create_page(self.context, timeout=30000)

            # Navigate to domain first (required to set cookies)
            self.log("Loading domain to inject cookies...", "INFO")
            self.page.goto(self.website_url, wait_until="domcontentloaded", timeout=30000)
            self.delay_ms(2000)

            # Inject cookies from FlareSolverr
            if self.cookies:
                # Convert FlareSolverr cookies to Playwright format
                playwright_cookies = []
                for cookie in self.cookies:
                    try:
                        cookie_dict = {
                            'name': cookie.get('name'),
                            'value': cookie.get('value'),
                            'domain': cookie.get('domain'),
                            'path': cookie.get('path', '/'),
                        }
                        if 'expiry' in cookie:
                            cookie_dict['expires'] = cookie['expiry']
                        if 'secure' in cookie:
                            cookie_dict['secure'] = cookie['secure']
                        if 'httpOnly' in cookie:
                            cookie_dict['httpOnly'] = cookie['httpOnly']
                        if 'sameSite' in cookie:
                            cookie_dict['sameSite'] = cookie['sameSite']
                        
                        playwright_cookies.append(cookie_dict)
                    except Exception as e:
                        self.log(f"Failed to convert cookie {cookie.get('name')}: {e}", "DEBUG")

                # Add all cookies at once
                if playwright_cookies:
                    self.context.add_cookies(playwright_cookies)
                    self.log(f"Injected {len(playwright_cookies)} cookies into browser", "SUCCESS")

            # Refresh page with cookies
            self.log("Reloading page with injected cookies...", "INFO")
            self.page.reload(wait_until="domcontentloaded", timeout=30000)
            self.delay_ms(3000)

            return True

        except Exception as e:
            self.log(f"Failed to initialize Playwright: {e}", "ERROR")
            return False

    def delay_ms(self, ms):
        """Delay in milliseconds"""
        time.sleep(ms / 1000)

    def scroll_to_element(self, locator):
        """Scroll element into view"""
        try:
            locator.scroll_into_view_if_needed()
            self.delay_ms(500)
        except:
            pass

    def click_element_js(self, selector, description):
        """Click element using JavaScript"""
        for attempt in range(self.max_retries):
            try:
                locator = self.page.locator(selector)
                locator.wait_for(state="visible", timeout=25000)
                self.scroll_to_element(locator)
                locator.evaluate("element => element.click()")
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
                    locator = self.page.locator(selector)
                    locator.wait_for(state="visible", timeout=10000)
                    self.log(f"Modal found with selector: {selector}", "INFO")
                    modal_found = True
                    break
                except:
                    continue

            if modal_found:
                self.delay_ms(3000)
                try:
                    self.page.locator('[data-testid="guest-selector-text"]').wait_for(state="visible", timeout=10000)
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
                container = self.page.locator('.SearchBarModalContainer')
                if container.count() > 0:
                    selector_text = container.locator('[data-testid="guest-selector-text"]')
            except:
                pass
            
            if selector_text is None or selector_text.count() == 0:
                try:
                    selector_text = self.page.locator('[data-testid="guest-selector-text"]')
                except:
                    return None

            if selector_text.count() > 0:
                text = selector_text.first.inner_text()
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
                container = self.page.locator('.SearchBarModalContainer')
                if container.count() > 0:
                    guest_selector = container.locator('[data-testid="guest-selector"]')
            except:
                pass
            
            if guest_selector is None or guest_selector.count() == 0:
                try:
                    guest_selector = self.page.locator('[data-testid="guest-selector"]')
                except:
                    self.log("Could not find guest selector", "ERROR")
                    return False

            self.page.locator('[data-testid="guest-selector-text"]').wait_for(state="visible", timeout=25000)
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
                plus_btn = guest_selector.locator('[data-testid="guest-selector_plus"]')
                minus_btn = guest_selector.locator('[data-testid="guest-selector_minus"]')
            except:
                self.log("Could not find plus/minus buttons", "ERROR")
                return False

            # Check if plus button is disabled
            plus_disabled = False
            try:
                if plus_btn.count() > 0:
                    plus_disabled = plus_btn.first.get_attribute("disabled") is not None
            except:
                pass

            if current_count < target_count and plus_disabled:
                self.log(f"Cannot increase to {target_count}. Max capacity reached.", "ERROR")
                return False

            iterations = 0
            max_iterations = 20

            while self.get_modal_guest_count() != target_count and iterations < max_iterations:
                current = self.get_modal_guest_count()

                if current < target_count:
                    if plus_btn.count() > 0:
                        plus_disabled = plus_btn.first.get_attribute("disabled") is not None
                        if not plus_disabled:
                            self.scroll_to_element(plus_btn.first)
                            plus_btn.first.evaluate("element => element.click()")
                            self.delay_ms(700)
                        else:
                            self.log(f"Cannot reach {target_count}", "ERROR")
                            return False
                elif current > target_count:
                    if minus_btn.count() > 0:
                        self.scroll_to_element(minus_btn.first)
                        minus_btn.first.evaluate("element => element.click()")
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

            self.page.locator('.ConsumerCalendar').wait_for(state="visible", timeout=25000)
            self.delay_ms(1500)

            date_found = False
            for attempt in range(4):
                try:
                    first_calendar = self.page.locator('[data-testid="calendar-first"]')
                    all_day_buttons = first_calendar.locator('button.ConsumerCalendar-day')

                    count = all_day_buttons.count()
                    self.log(f"Found {count} day buttons", "INFO")

                    for i in range(count):
                        try:
                            btn = all_day_buttons.nth(i)
                            day_span = btn.locator('span')
                            if day_span.count() > 0:
                                day_text = day_span.first.inner_text().strip()

                                if day_text == day:
                                    btn_classes = btn.get_attribute('class') or ''
                                    is_disabled = 'is-disabled' in btn_classes or btn.get_attribute('disabled') is not None

                                    if not is_disabled and 'is-in-month' in btn_classes:
                                        self.log(f"Clicking date {day}...", "SUCCESS")
                                        self.scroll_to_element(btn)
                                        self.delay_ms(500)
                                        btn.evaluate("element => element.click()")
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

            self.page.locator('[data-testid="search-result"]').first.wait_for(state="visible", timeout=25000)
            self.delay_ms(2000)

            time_elements = self.page.locator('[data-testid="search-result"]')
            count = time_elements.count()
            self.log(f"Found {count} time slots", "INFO")

            for i in range(count):
                try:
                    element = time_elements.nth(i)
                    time_elem = element.locator('[data-testid="search-result-time"]')
                    if time_elem.count() > 0:
                        time_text = time_elem.first.inner_text().strip()

                        availability_text = "Available"
                        try:
                            availability_elem = element.locator('[data-testid="communal-count-text"]')
                            if availability_elem.count() > 0:
                                availability_text = availability_elem.first.inner_text().strip()
                        except:
                            pass

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
            print(f"{i:<4} {slot['time']:<15} {slot.get('availability', slot.get('price', '')):<30}")
        print("=" * 60 + "\n")

    def run(self):
        """Main automation flow"""
        try:
            self.log("Starting Exploretock Automation (FlareSolverr + Playwright)", "START")

            # Step 1: Bypass Cloudflare with FlareSolverr
            self.log("Step 1: Bypassing Cloudflare with FlareSolverr", "STEP")
            if not self.create_flaresolverr_session():
                self.log("Failed to bypass Cloudflare", "ERROR")
                return False

            # Step 2: Initialize Playwright with cookies
            self.log("Step 2: Initializing Playwright with cookies", "STEP")
            if not self.init_playwright_with_cookies():
                self.log("Failed to initialize Playwright", "ERROR")
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
            self.cleanup()

    def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                self.page.close()
                self.page = None
        except Exception as e:
            logger.warning(f"Error closing page: {e}")

        try:
            if self.context:
                self.context.close()
                self.context = None
        except Exception as e:
            logger.warning(f"Error closing context: {e}")

        try:
            if self.browser:
                self.browser.close()
                self.browser = None
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")


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
        automation.cleanup()
                
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
    print("\n   2. Playwright browsers installed")
    print("      playwright install chromium")
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
