from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HijingoBookingBot:
    def __init__(self, headless=True):
        """
        Initialize the bot
        :param headless: Run in headless mode (for servers without display)
        """
        options = webdriver.ChromeOptions()

        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            print("🖥️ Running in HEADLESS mode")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        else:
            self.driver = webdriver.Chrome()
            self.driver.maximize_window()

        self.wait = WebDriverWait(self.driver, 10)

    def start_booking(self, guests, booking_date):
        """
        Main booking function
        :param guests: Number of guests (e.g., 6)
        :param booking_date: Date in format "YYYY-MM-DD" (e.g., "2025-12-25") or "MM/DD/YYYY" (e.g., "12/25/2025")
        """
        try:
            # Convert booking_date to YYYY-MM-DD format
            if '/' in booking_date:
                # Handle MM/DD/YYYY format
                parts = booking_date.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    target_date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                else:
                    # Legacy MM/DD format - assume current year
                    month, day = parts
                    from datetime import datetime
                    year = datetime.now().year
                    target_date_str = f"{year}-{int(month):02d}-{int(day):02d}"
            elif '-' in booking_date:
                # Already in YYYY-MM-DD format
                target_date_str = booking_date
            else:
                raise ValueError(f"Invalid date format: {booking_date}. Use YYYY-MM-DD or MM/DD/YYYY")
            
            # Construct URL with date and guests
            url = f"https://www.hijingo.com/book?depart={target_date_str}&guests={guests}"
            print(f"🌐 Opening URL: {url}")
            self.driver.get(url)
            time.sleep(4)

            try:
                self.driver.save_screenshot('/home/faizan/Documents/debug_screenshot.png')
                print(f"📸 Screenshot saved")
            except:
                pass
            print(f"📄 Page title: {self.driver.title}")
            print(f"🔗 Current URL: {self.driver.current_url}")

            self.handle_cookie_consent()
            time.sleep(2)

            # Check if date is available by looking for the date header
            date_available = self.check_date_availability(target_date_str)

            # If date is not available, stop execution
            if not date_available:
                print(f"\n❌ Date {booking_date} is not available. Stopping execution.")
                return

            slots_data = self.scrape_slots(target_date_str)

            if not slots_data:
                print(f"\n❌ No available slots for date {booking_date}.")
                return

            self.display_slots(slots_data, booking_date)

            print("✅ Scraping completed!")

        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            import traceback
            traceback.print_exc()

    def handle_cookie_consent(self):
        """Click the 'Allow All' button for cookie consent if it appears"""
        try:
            print("🍪 Checking for cookie consent banner...")

            cookie_button_xpath = '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'

            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
            )

            cookie_button.click()
            print("✓ Clicked 'Allow All' on cookie consent")
            time.sleep(1)

        except TimeoutException:
            print("ℹ️ No cookie consent banner found - continuing...")
        except Exception as e:
            print(f"ℹ️ Cookie consent handling: {str(e)}")

    def check_date_availability(self, target_date_str):
        """Check if the target date is available by looking for the date header. Returns False if date unavailable."""
        try:
            print(f"📅 Checking availability for date: {target_date_str}")

            # Wait a bit for the page to load with the date pre-selected
            time.sleep(3)

            # Check if the date header exists in the slots list
            date_header_selector = f'li.slot-search__item--date[data-date="{target_date_str}"]'

            try:
                date_header = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, date_header_selector))
                )
                print(f"✓ Date {target_date_str} is available")
                return True

            except TimeoutException:
                print(f"⚠️ Date {target_date_str} not found - slot not available")
                return False

        except Exception as e:
            print(f"✗ Failed to check date availability: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def scrape_slots(self, target_date):
        """Scrape available time slots for ONLY the specific target date (excluding sold out)"""
        try:
            print(f"🕐 Scraping time slots for {target_date} only...")

            time.sleep(3)

            # Find the date header for the target date
            date_header_selector = f'li.slot-search__item--date[data-date="{target_date}"]'

            try:
                # Verify the date header exists
                date_header = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, date_header_selector))
                )
                print(f"✓ Found date header for {target_date}")

                # Get all list items
                all_list_items = self.driver.find_elements(By.CSS_SELECTOR, '.slot-search__list > li')

                slots_data = []
                collecting = False

                for item in all_list_items:
                    # Check if this is a date header
                    is_date_header = 'slot-search__item--date' in item.get_attribute('class')

                    if is_date_header:
                        # Get the data-date attribute
                        item_date = item.get_attribute('data-date')

                        # Start collecting when we reach our target date
                        if item_date == target_date:
                            collecting = True
                            print(f"✓ Started collecting slots for {target_date}")
                            continue
                        # Stop collecting when we reach the next date
                        elif collecting:
                            print(f"✓ Reached next date ({item_date}), stopping collection")
                            break
                        else:
                            continue

                    # Only process slots when we're collecting for our target date
                    if not collecting:
                        continue

                    try:
                        # Check if this slot contains a date card (actual slot) vs empty list item
                        date_card = item.find_elements(By.CSS_SELECTOR, '.date-card')
                        if not date_card:
                            continue

                        # Check if slot is sold out
                        is_sold_out = 'date-card--sold-out' in date_card[0].get_attribute('class')
                        if is_sold_out:
                            print(f"⊗ Skipping sold out slot")
                            continue

                        # Extract time from span.item-dates
                        time_element = item.find_element(By.CSS_SELECTOR, '.item-dates')
                        time_text = time_element.text.strip()

                        # Extract price
                        try:
                            price_element = item.find_element(By.CSS_SELECTOR, '.js-price-string-price')
                            price_text = price_element.text.strip()
                        except:
                            price_text = "Price not available"

                        # Get event type (X.MAS, Hijingo OG, etc.)
                        try:
                            event_element = item.find_element(By.CSS_SELECTOR, '.p--xsmall.weight-bold')
                            event_text = event_element.text.strip()
                        except:
                            event_text = "Standard"

                        # Check for special badge (free cocktail offer, etc.)
                        try:
                            badge_element = item.find_element(By.CSS_SELECTOR, '.date-card__badge.override-badge')
                            badge_text = badge_element.text.strip()
                        except:
                            badge_text = None

                        # Check for "Last few" or other badges
                        availability_status = "Available"
                        try:
                            low_stock_badge = item.find_element(By.CSS_SELECTOR, '.date-card__badge.low-stock')
                            availability_status = low_stock_badge.text.strip()
                        except:
                            pass

                        slot_info = {
                            'time': time_text,
                            'price': price_text,
                            'event': event_text,
                            'availability': availability_status
                        }

                        if badge_text:
                            slot_info['special_offer'] = badge_text

                        slots_data.append(slot_info)

                    except Exception as e:
                        print(f"⚠️ Could not extract data for slot: {str(e)}")
                        continue

                print(f"✓ Found {len(slots_data)} available time slots for {target_date}")
                return slots_data

            except TimeoutException:
                print(f"⚠️ No time slots found for date {target_date}")
                return []

        except Exception as e:
            print(f"✗ Failed to scrape slots: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def display_slots(self, slots_data, booking_date):
        """Display the scraped slots data in a formatted way"""
        if not slots_data:
            print("\n❌ No slots available for the selected date")
            return

        print(f"\n{'=' * 70}")
        print(f"📅 Available Slots for {booking_date}")
        print(f"{'=' * 70}\n")

        for index, slot in enumerate(slots_data, 1):
            print(f"Slot {index}:")
            print(f"  🕐 Time:         {slot['time']}")
            print(f"  💰 Price:        {slot['price']}")
            print(f"  🎉 Event:        {slot['event']}")
            print(f"  📊 Availability: {slot['availability']}")
            if 'special_offer' in slot:
                print(f"  🎁 Special:      {slot['special_offer']}")
            print(f"{'-' * 70}")

        print(f"\n✅ Total available slots: {len(slots_data)}\n")

    def close(self):
        """Close the browser"""
        print("🔚 Closing browser in 10 seconds...")
        time.sleep(10)
        self.driver.quit()


def scrape_hijingo(guests, target_date):
    """
    Scrape Hijingo availability slots
    :param guests: Number of guests (e.g., 6)
    :param target_date: Date in format "YYYY-MM-DD" (e.g., "2025-12-25")
    :return: List of slot dictionaries in app format
    """
    bot = None
    results = []
    
    try:
        logger.info(f"[Hijingo] Starting scrape for {guests} guests on {target_date}")
        bot = HijingoBookingBot(headless=True)
        
        # Convert target_date to YYYY-MM-DD format if needed
        if '/' in target_date:
            # Handle MM/DD/YYYY format
            parts = target_date.split('/')
            if len(parts) == 3:
                month, day, year = parts
                target_date_str = f"{year}-{int(month):02d}-{int(day):02d}"
            else:
                # Legacy MM/DD format - assume current year
                month, day = parts
                from datetime import datetime
                year = datetime.now().year
                target_date_str = f"{year}-{int(month):02d}-{int(day):02d}"
        elif '-' in target_date:
            # Already in YYYY-MM-DD format
            target_date_str = target_date
        else:
            raise ValueError(f"Invalid date format: {target_date}. Use YYYY-MM-DD or MM/DD/YYYY")
        
        # Construct URL with date and guests
        url = f"https://www.hijingo.com/book?depart={target_date_str}&guests={guests}"
        logger.info(f"[Hijingo] Opening URL: {url}")
        bot.driver.get(url)
        time.sleep(4)
        
        # Handle cookie consent
        bot.handle_cookie_consent()
        time.sleep(2)
        
        # Check if date is available
        date_available = bot.check_date_availability(target_date_str)
        
        if not date_available:
            logger.warning(f"[Hijingo] Date {target_date_str} is not available")
            return results
        
        # Scrape slots
        slots_data = bot.scrape_slots(target_date_str)
        
        if not slots_data:
            logger.info(f"[Hijingo] No available slots for date {target_date_str}")
            return results
        
        # Convert to app format
        for slot in slots_data:
            # Map availability status
            status = slot.get('availability', 'Available')
            if status == 'Available':
                status = 'Available'
            elif 'Last few' in status or 'Low stock' in status:
                status = 'Available'  # Still available, just low stock
            else:
                status = 'Available'  # Default to Available
            
            result_item = {
                'date': target_date_str,
                'time': slot.get('time', ''),
                'price': slot.get('price', 'Price not available'),
                'status': status,
                'website': 'Hijingo',
                'guests': guests,
                'timestamp': datetime.now().isoformat(),
            }
            
            # Add event type if available
            if slot.get('event'):
                result_item['description'] = slot.get('event')
            
            # Add special offer if available
            if slot.get('special_offer'):
                if 'description' in result_item:
                    result_item['description'] += f" - {slot.get('special_offer')}"
                else:
                    result_item['description'] = slot.get('special_offer')
            
            results.append(result_item)
        
        logger.info(f"[Hijingo] Found {len(results)} available slots")
        return results
        
    except Exception as e:
        logger.error(f"[Hijingo] Error during scraping: {str(e)}", exc_info=True)
        return results
    finally:
        if bot:
            try:
                bot.driver.quit()
            except:
                pass


# Usage example
if __name__ == "__main__":
    bot = HijingoBookingBot(headless= True)  # Change to True for headless mode

    try:
        guests = 4
        booking_date = "2025-12-31"  # Format: YYYY-MM-DD

        bot.start_booking(guests, booking_date)

    finally:
        bot.close()
