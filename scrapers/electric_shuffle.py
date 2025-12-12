"""
Electric Shuffle scraper (NYC and London) using Playwright
"""
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


# def scrape_electric_shuffle(guests, target_date):
#     """Electric Shuffle NYC scraper function"""
#     results = []
    
#     try:
#         url = f"https://www.sevenrooms.com/explore/electricshufflenyc/reservations/create/search/?date={str(target_date)}&halo=120&party_size={str(guests)}&start_time=ALL"
        
#         with BaseScraper() as scraper:
#             scraper.goto(url, timeout=60000, wait_until="networkidle")
#             scraper.wait_for_timeout(8000)  # Wait for page to fully render
            
#             try:
#                 scraper.wait_for_selector('span[data-test="reservation-timeslot-button-description"]', timeout=45000)
#                 scraper.wait_for_timeout(3000)  # Additional wait for slots to be fully loaded
#             except Exception:
#                 logger.info('No slots available on Electric Shuffle NYC or page took too long to load')
#                 return results
            
#             content = scraper.get_content()
#             soup = BeautifulSoup(content, "html.parser")
#             slots = soup.find_all('div', {'class': 'sc-imWYAI cTOWnZ'})
            
#             if len(slots) == 0:
#                 logger.info('No slots available on Electric Shuffle NYC')
#                 return results
            
#             logger.info(f'Found {len(slots)} available slots on Electric Shuffle NYC')
            
#             for slot in slots:
#                 status = "Available"
                
#                 try:
#                     time = slot.find('div').get_text().strip()
#                 except:
#                     time = "None"
                
#                 try:
#                     length = slot.get_text().strip()
#                 except:
#                     length = "None"
                
#                 slot_data = {
#                     'date': target_date,
#                     'time': time,
#                     'price': length,
#                     'status': status,
#                     'timestamp': datetime.now().isoformat(),
#                     'website': 'Electric Shuffle (NYC)'
#                 }
#                 results.append(slot_data)
        
#         return results
        
#     except Exception as e:
#         logger.error(f"Error scraping Electric Shuffle NYC: {e}", exc_info=True)
#         raise e


def scrape_electric_shuffle(guests, target_date):
    """Electric Shuffle NYC scraper function"""
    results = []

    try:
        url = (
            f"https://www.sevenrooms.com/explore/electricshufflenyc/"
            f"reservations/create/search/?date={str(target_date)}&halo=120&"
            f"party_size={str(guests)}&start_time=ALL"
        )

        with BaseScraper() as scraper:

            # ---- LOAD PAGE (FORCED STOP AFTER 4 SEC) ----
            try:
                scraper.goto(url, timeout=5000, wait_until="domcontentloaded")
            except:
                pass  # page still loads in background

            # scraper.page.evaluate("window.stop()")   # STOP loading

            # Wait for slots container
            try:
                scraper.wait_for_selector(
                    'div[data-test="reservation-availability-grid-primary"]',
                    timeout=15000
                )
            except:
                logger.info("No slots available on Electric Shuffle NYC")
                return results

            scraper.wait_for_timeout(2000)  # allow JS to populate

            # ---- PARSE SLOTS ----
            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            container = soup.find("div", {
                "data-test": "reservation-availability-grid-primary"
            })
            if not container:
                logger.info("Slots container not found")
                return results

            # Each slot wrapper
            slots = container.find_all("div", {"class": "sc-imWYAI cTOWnZ"})

            if not slots:
                logger.info("No slots found inside container")
                return results

            logger.info(f"Found {len(slots)} slot containers")

            # OPTIONAL: skip first slot
            # slots = slots[1:]

            for slot in slots:
                btn = slot.find("button")
                if not btn:
                    continue

                # Extract time
                time_el = btn.find("span", {
                    "data-test": "reservation-timeslot-button-time"
                })
                time_str = time_el.get_text(strip=True) if time_el else "None"

                # Extract description (Brunch Social / Classic Shuffle)
                desc_el = btn.find("span", {
                    "data-test": "reservation-timeslot-button-description"
                })
                desc_str = desc_el.get_text(strip=True) if desc_el else "None"

                slot_data = {
                    "date": target_date,
                    "time": time_str,
                    "price": desc_str,      # Using description as price/value
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": "Electric Shuffle (NYC)"
                }

                results.append(slot_data)

        return results

    except Exception as e:
        logger.error(f"Error scraping Electric Shuffle NYC: {e}", exc_info=True)
        raise e



# def scrape_electric_shuffle_london(guests, target_date):
#     """Electric Shuffle London scraper function"""
#     results = []
    
#     try:
#         url = (
#             "https://electricshuffle.com/uk/london/book/shuffleboard?"
#             f"preferedvenue=7&preferedtime=23%3A00&guestQuantity={guests}&date={target_date}"
#         )
        
#         with BaseScraper() as scraper:
#             scraper.goto(url, timeout=60000, wait_until="networkidle")
#             scraper.wait_for_timeout(8000)  # Wait for page to fully render
            
#             # Wait for time slots container to appear
#             try:
#                 scraper.wait_for_selector('button.time-slot, div.slot, [class*="time-slot"], [class*="slot"]', timeout=45000)
#                 scraper.wait_for_timeout(3000)  # Additional wait for slots to be fully loaded
#             except Exception:
#                 logger.warning("Time slot elements not found, continuing anyway...")
            
#             content = scraper.get_content()
#             soup = BeautifulSoup(content, "html.parser")
            
#             # Find available time slots
#             # This selector may need adjustment based on actual page structure
#             slots = soup.find_all('button', {'class': 'time-slot'}) or soup.find_all('div', {'class': 'slot'})
            
#             for slot in slots:
#                 try:
#                     time = slot.get_text().strip()
#                 except:
#                     time = "None"
                
#                 slot_data = {
#                     'date': target_date,
#                     'time': time,
#                     'price': 'N/A',
#                     'status': 'Available',
#                     'timestamp': datetime.now().isoformat(),
#                     'website': 'Electric Shuffle (London)'
#                 }
#                 results.append(slot_data)
        
#         return results
        
#     except Exception as e:
#         logger.error(f"Error scraping Electric Shuffle London: {e}", exc_info=True)
#         raise e





def scrape_electric_shuffle_london(guests, target_date):
    """Electric Shuffle London scraper function (Playwright version)"""
    results = []

    try:
        # Electric Shuffle London booking URL
        url = (
            "https://electricshuffle.com/uk/london/book/shuffleboard?"
            f"preferedvenue=7&preferedtime=23%3A00&guestQuantity={guests}&date={target_date}"
        )

        with BaseScraper() as scraper:

            # ---- LOAD PAGE QUICKLY + FORCE STOP ----
            try:
                scraper.goto(url, timeout=15000, wait_until="domcontentloaded")
            except:
                pass

            # scraper.page.evaluate("window.stop()")
            scraper.wait_for_timeout(5000)

            # ---- WAIT FOR VENUE BLOCKS ----
            try:
                scraper.wait_for_selector(
                    "form.es_booking__availability__form",
                    timeout=15000
                )
            except Exception:
                logger.info("No venue availability sections found.")
                return results

            scraper.wait_for_timeout(5000)

            # ---- PARSE HTML ----
            content = scraper.get_content()
            soup = BeautifulSoup(content, "html.parser")

            # All venue availability blocks
            holders = soup.select("form.es_booking__availability__form")

            if not holders:
                logger.info("No venue sections found.")
                return results

            # ---- LOOP THROUGH VENUES ----
            for holder in holders:

                # Venue Name
                title_el = holder.select_one(
                    "div.es_booking__availability-header.es_font-body--semi-bold"
                )
                venue_name = (
                    title_el.get_text(strip=True) if title_el else "Unknown Venue"
                )

                # All time-slot wrappers in this venue
                slots = holder.select("div.es_booking__availability__table-cell__wrapper")

                for slot in slots:

                    # ---- Extract the time ("name" attribute) ----
                    try:
                        time_val = slot.select_one(
                            "div.es_booking__availability__table-cell"
                        )["name"]
                    except:
                        time_val = "None"

                    # ---- Extract details (duration + price + availability) ----
                    desc_parts = []
                    wrap = slot.select_one("div.es_booking__time_wrapper")

                    if wrap:
                        inputs = wrap.select("input.es_booking__availability__time-slot")

                        for inp in inputs:
                            label = inp.find_next("label")

                            # Duration
                            dur_el = label.select_one(".es_booking__availability__duration")
                            duration = (
                                dur_el.get_text(strip=True).replace("mins", "min")
                                if dur_el
                                else None
                            )

                            # Price
                            price_el = label.select_one(
                                ".es_booking__availability__price-per-person"
                            )
                            price = price_el.get_text(strip=True) if price_el else None

                            # Unavailable?
                            if inp.has_attr("disabled"):
                                desc_parts.append("unavailable")
                            else:
                                if duration and price:
                                    desc_parts.append(f"{duration} {price}")
                                elif duration:
                                    desc_parts.append(duration)
                                else:
                                    desc_parts.append("available")

                    details = ", ".join(desc_parts) if desc_parts else "unavailable"

                    # ---- Store slot ----
                    slot_data = {
                        "venue": venue_name,
                        "date": target_date,
                        "time": time_val,
                        "details": details,
                        "timestamp": datetime.now().isoformat(),
                        "website": "Electric Shuffle (London)",
                    }

                    results.append(slot_data)

        return results

    except Exception as e:
        logger.error(f"Error scraping Electric Shuffle London: {e}", exc_info=True)
        raise e
