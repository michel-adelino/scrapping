from playwright.sync_api import Browser, BrowserContext, Page
import time
import logging
from datetime import datetime
from browser_utils import create_browser, create_browser_context, create_page, create_browser_with_context

logger = logging.getLogger(__name__)


class HijingoBookingBot:
    def __init__(self, headless=True):
        """
        Initialize the bot
        :param headless: Run in headless mode (for servers without display)
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
        # Create browser with context
        self.browser, self.context = create_browser_with_context(
            headless=headless,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Create page
        self.page = create_page(self.context, timeout=30000)
        
        # Hide webdriver property
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        
        if headless:
            print("🖥️ Running in HEADLESS mode")

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
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)

            try:
                self.page.screenshot(path='/home/faizan/Documents/debug_screenshot.png')
                print(f"📸 Screenshot saved")
            except:
                pass
            print(f"📄 Page title: {self.page.title()}")
            print(f"🔗 Current URL: {self.page.url}")

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

            try:
                cookie_button = self.page.locator(cookie_button_xpath)
                cookie_button.wait_for(state="visible", timeout=5000)
                cookie_button.click()
                print("✓ Clicked 'Allow All' on cookie consent")
                time.sleep(1)
            except:
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
                date_header = self.page.locator(date_header_selector)
                date_header.wait_for(state="visible", timeout=10000)
                print(f"✓ Date {target_date_str} is available")
                return True

            except:
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
                date_header = self.page.locator(date_header_selector)
                date_header.wait_for(state="visible", timeout=10000)
                print(f"✓ Found date header for {target_date}")

                # Get all list items
                all_list_items = self.page.locator('.slot-search__list > li')
                count = all_list_items.count()

                slots_data = []
                collecting = False

                for i in range(count):
                    item = all_list_items.nth(i)
                    
                    # Check if this is a date header
                    item_classes = item.get_attribute('class') or ''
                    is_date_header = 'slot-search__item--date' in item_classes

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
                        date_card = item.locator('.date-card')
                        if date_card.count() == 0:
                            continue

                        # Check if slot is sold out
                        date_card_classes = date_card.first.get_attribute('class') or ''
                        is_sold_out = 'date-card--sold-out' in date_card_classes
                        if is_sold_out:
                            print(f"⊗ Skipping sold out slot")
                            continue

                        # Extract time from span.item-dates
                        time_element = item.locator('.item-dates')
                        if time_element.count() > 0:
                            time_text = time_element.first.inner_text().strip()
                        else:
                            continue

                        # Extract price
                        try:
                            price_element = item.locator('.js-price-string-price')
                            if price_element.count() > 0:
                                price_text = price_element.first.inner_text().strip()
                            else:
                                price_text = "Price not available"
                        except:
                            price_text = "Price not available"

                        # Get event type (X.MAS, Hijingo OG, etc.)
                        try:
                            event_element = item.locator('.p--xsmall.weight-bold')
                            if event_element.count() > 0:
                                event_text = event_element.first.inner_text().strip()
                            else:
                                event_text = "Standard"
                        except:
                            event_text = "Standard"

                        # Check for special badge (free cocktail offer, etc.)
                        try:
                            badge_element = item.locator('.date-card__badge.override-badge')
                            if badge_element.count() > 0:
                                badge_text = badge_element.first.inner_text().strip()
                            else:
                                badge_text = None
                        except:
                            badge_text = None

                        # Check for "Last few" or other badges
                        availability_status = "Available"
                        try:
                            low_stock_badge = item.locator('.date-card__badge.low-stock')
                            if low_stock_badge.count() > 0:
                                availability_status = low_stock_badge.first.inner_text().strip()
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

            except:
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
        bot.page.goto(url, wait_until="domcontentloaded", timeout=30000)
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
                bot.cleanup()
            except:
                pass


# Usage example
if __name__ == "__main__":
    bot = HijingoBookingBot(headless=True)  # Change to True for headless mode

    try:
        guests = 4
        booking_date = "2025-12-31"  # Format: YYYY-MM-DD

        bot.start_booking(guests, booking_date)

    finally:
        bot.close()
