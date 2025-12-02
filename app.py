from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from seleniumbase import Driver
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import re
import os
from urllib.parse import quote_plus, urlencode
from celery import group, chord
from celery.result import AsyncResult
from sqlalchemy import inspect, text, or_

from models import db, AvailabilitySlot, ScrapingTask

# Import celery_app after app is created to avoid circular import
# We'll import it in the tasks that need it
try:
    from celery_app import celery_app
except ImportError:
    # Fallback if celery_app not available
    celery_app = None

app = Flask(__name__)


def find_chrome_binary():
    """Find Chrome/Chromium binary in common locations"""
    import shutil
    import platform
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Common Chrome binary locations
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/local/bin/google-chrome',
        '/usr/local/bin/chromium-browser',
        '/usr/local/bin/chromium',
        '/snap/bin/chromium',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # Windows
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',  # Windows
    ]
    
    # Check if chrome is in PATH
    chrome_in_path = shutil.which('google-chrome') or shutil.which('chromium-browser') or shutil.which('chromium')
    if chrome_in_path:
        logger.info(f"[CHROME] Found Chrome binary in PATH: {chrome_in_path}")
        return chrome_in_path
    
    # Check common locations
    for path in chrome_paths:
        if os.path.exists(path):
            logger.info(f"[CHROME] Found Chrome binary at: {path}")
            return path
    
    # Check environment variable
    chrome_env = os.getenv('CHROME_BINARY') or os.getenv('GOOGLE_CHROME_BIN')
    if chrome_env and os.path.exists(chrome_env):
        logger.info(f"[CHROME] Found Chrome binary from env: {chrome_env}")
        return chrome_env
    
    logger.warning("[CHROME] Chrome binary not found!")
    return None

def verify_chrome_installation():
    """Verify Chrome is installed and can run (on Linux)"""
    import platform
    import subprocess
    import logging
    
    logger = logging.getLogger(__name__)
    
    if platform.system() != 'Linux':
        return True  # Skip verification on non-Linux systems
    
    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        logger.error("[CHROME] Chrome binary not found!")
        return False
    
    # Try to run Chrome with --version to verify it works
    try:
        logger.info(f"[CHROME] Verifying Chrome installation at: {chrome_binary}")
        result = subprocess.run(
            [chrome_binary, '--version', '--headless', '--no-sandbox', '--disable-gpu'],
            capture_output=True,
            timeout=10,
            text=True
        )
        if result.returncode == 0 or 'Chrome' in result.stdout or 'Chromium' in result.stdout:
            logger.info(f"[CHROME] Chrome verification successful: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"[CHROME] Chrome verification returned non-zero: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("[CHROME] Chrome verification timed out!")
        return False
    except Exception as e:
        logger.error(f"[CHROME] Chrome verification failed: {str(e)}")
        return False


def create_driver_with_timeout(uc, driver_kwargs, timeout=60):
    """
    Create Driver with a timeout to prevent indefinite hanging.
    Uses threading to enforce timeout.
    """
    import threading
    import logging
    import queue
    
    logger = logging.getLogger(__name__)
    result_queue = queue.Queue()
    exception_queue = queue.Queue()
    
    def create_driver():
        try:
            logger.info(f"[DRIVER] Starting Driver creation...")
            driver = Driver(
                uc=False,
                headless2=False,
                no_sandbox=True,
                disable_gpu=True,
                headed=True,
            )
            logger.info(f"[DRIVER] Driver created successfully")
            result_queue.put(driver)
        except Exception as e:
            logger.error(f"[DRIVER] Exception during Driver creation: {str(e)}")
            exception_queue.put(e)
    
    thread = threading.Thread(target=create_driver, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        logger.error(f"[DRIVER] Driver creation timed out after {timeout} seconds!")
        raise TimeoutError(f"Driver creation timed out after {timeout} seconds")
    
    if not exception_queue.empty():
        raise exception_queue.get()
    
    if not result_queue.empty():
        return result_queue.get()
    
    raise RuntimeError("Driver creation failed for unknown reason")

def create_driver_safe(uc=True, headless2=True, no_sandbox=True, disable_gpu=True, **extra_kwargs):
    """
    Create SeleniumBase Driver with standard configuration.
    Uses standard config: uc=False, headless2=False, no_sandbox=True, disable_gpu=True, headed=True
    """
    import platform
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    
    # On Linux, verify Chrome installation first
    if platform.system() == 'Linux':
        print("[DRIVER] Verifying Chrome installation on Linux...", flush=True)
        logger.info("[DRIVER] Verifying Chrome installation on Linux...")
        if not verify_chrome_installation():
            raise RuntimeError("Chrome is not properly installed or cannot run on this system")
        print("[DRIVER] Chrome verification passed", flush=True)
        logger.info("[DRIVER] Chrome verification passed")
    
    print("[DRIVER] Creating Chrome driver with standard configuration...", flush=True)
    logger.info("[DRIVER] Creating Chrome driver with standard configuration...")
    
    # Create driver with standard configuration
    driver = create_driver_with_timeout(uc=False, driver_kwargs={}, timeout=60)
    print("[DRIVER] Driver created successfully!", flush=True)
    logger.info("[DRIVER] Driver created successfully")
    
    # On Linux, wait a moment for Chrome to fully initialize
    if platform.system() == 'Linux':
        time.sleep(1)
    # Set page load timeout to prevent hanging
    driver.set_page_load_timeout(30)
    return driver

def create_driver_with_chrome_fallback(**kwargs):
    """Create SeleniumBase Driver with Chrome binary detection and fallback"""
    import platform
    import logging
    
    logger = logging.getLogger(__name__)
    chrome_binary = find_chrome_binary()
    
    # Create driver with standard configuration
    logger.info("[DRIVER] Creating driver with standard configuration...")
    driver = Driver(
        uc=False,
        headless2=False,
        no_sandbox=True,
        disable_gpu=True,
        headed=True,
    )
    logger.info("[DRIVER] Driver created successfully")
    # On Linux, wait a moment for Chrome to fully initialize
    if platform.system() == 'Linux':
        import time
        time.sleep(1)
    # Set page load timeout to prevent hanging
    driver.set_page_load_timeout(30)
    return driver

# Enable CORS for React frontend
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins in development

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "availability.db")}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables and ensure latest schema
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('availability_slots')]
    if 'booking_url' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE availability_slots ADD COLUMN booking_url VARCHAR(500)"))


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

# Global variables for scraping status and data
scraping_status = {
    'running': False,
    'progress': 'Ready',
    'completed': False,
    'error': None,
    'total_slots_found': 0,
    'current_date': None,
    'website': None
}
scraped_data = []

# City venue lists for multi-venue scraping
NYC_VENUES = [
    'swingers_nyc',
    'electric_shuffle_nyc',
    'lawn_club_nyc',
    'spin_nyc',
    'five_iron_golf_nyc',
    'lucky_strike_nyc',
    'easybowl_nyc'
]

LONDON_VENUES = [
    'swingers_london',
    'electric_shuffle_london',
    'fair_game_canary_wharf',
    'fair_game_city',
    'clays_bar',
    'puttshack',
    'flight_club_darts',
    'flight_club_darts_angel',
    'flight_club_darts_shoreditch',
    'flight_club_darts_victoria',
    'f1_arcade'
]

VENUE_BOOKING_URLS = {
    'Swingers (NYC)': 'https://www.swingers.club/us/locations/nyc/book-now',
    'Swingers (London)': 'https://www.swingers.club/uk/book-now',
    'Electric Shuffle (NYC)': 'https://www.sevenrooms.com/explore/electricshufflenyc/reservations/create/search',
    'Electric Shuffle (London)': 'https://electricshuffle.com/uk/london/book',
    'Lawn Club NYC': 'https://www.sevenrooms.com/landing/lawnclubnyc',
    'SPIN (NYC)': 'https://wearespin.com/location/new-york-flatiron/table-reservations/',
    'Five Iron Golf (NYC)': 'https://booking.fiveirongolf.com/session-length',
    'Lucky Strike (NYC)': 'https://www.luckystrikeent.com/location/lucky-strike-chelsea-piers/booking/lane-reservation',
    'Easybowl (NYC)': 'https://www.easybowl.com/bc/LET/booking',
    'Fair Game (Canary Wharf)': 'https://www.sevenrooms.com/explore/fairgame/reservations/create/search',
    'Fair Game (City)': 'https://www.sevenrooms.com/explore/fairgamecity/reservations/create/search',
    'Clays Bar (Canary Wharf)': 'https://clays.bar/book',
    'Clays Bar (The City)': 'https://clays.bar/book',
    'Clays Bar (Birmingham)': 'https://clays.bar/book',
    'Clays Bar (Soho)': 'https://clays.bar/book',
    'Puttshack (Bank)': 'https://www.puttshack.com/book-golf',
    'Puttshack (Lakeside)': 'https://www.puttshack.com/book-golf',
    'Puttshack (White City)': 'https://www.puttshack.com/book-golf',
    'Puttshack (Watford)': 'https://www.puttshack.com/book-golf',
    'Flight Club Darts': 'https://flightclubdarts.com/book',
    'Flight Club Darts (Angel)': 'https://flightclubdarts.com/book',
    'Flight Club Darts (Shoreditch)': 'https://flightclubdarts.com/book',
    'Flight Club Darts (Victoria)': 'https://flightclubdarts.com/book',
    'F1 Arcade': 'https://f1arcade.com/uk/booking/venue/london'
}


def build_booking_search_url(venue_name):
    if not venue_name:
        return None
    query = quote_plus(f"{venue_name} booking")
    return f"https://www.google.com/search?q={query}"


def get_booking_url_for_venue(venue_name, explicit_url=None):
    """Return the deepest known booking URL for a venue, or fall back to search."""
    if explicit_url:
        return explicit_url
    if not venue_name:
        return None
    # Direct match
    if venue_name in VENUE_BOOKING_URLS:
        return VENUE_BOOKING_URLS[venue_name]
    # Attempt normalized match (strip city details)
    normalized = venue_name.split('(')[0].strip()
    for known_name, url in VENUE_BOOKING_URLS.items():
        if normalized and normalized.lower() in known_name.lower():
            return url
    return build_booking_search_url(venue_name)


# Helper function to save slot to database
def save_slot_to_db(venue_name, date_str, time, price, status, guests, city, venue_specific_data=None, booking_url=None):
    """Save or update availability slot in database"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date() if isinstance(date_str, str) else date_str
        effective_booking_url = get_booking_url_for_venue(venue_name, booking_url)
        
        # Check if slot already exists
        existing = AvailabilitySlot.query.filter_by(
            venue_name=venue_name,
            date=date_obj,
            time=time,
            guests=guests
        ).first()
        
        if existing:
            # Update existing record
            existing.price = price
            existing.status = status
            existing.last_updated = datetime.utcnow()
            if effective_booking_url and existing.booking_url != effective_booking_url:
                existing.booking_url = effective_booking_url
            if venue_specific_data:
                existing.set_venue_specific_data(venue_specific_data)
            db.session.commit()
            return existing
        else:
            # Create new record
            slot = AvailabilitySlot(
                venue_name=venue_name,
                date=date_obj,
                time=time,
                price=price,
                status=status,
                guests=guests,
                city=city,
                booking_url=effective_booking_url,
                timestamp=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            if venue_specific_data:
                slot.set_venue_specific_data(venue_specific_data)
            db.session.add(slot)
            db.session.commit()
            return slot
    except Exception as e:
        db.session.rollback()
        print(f"Error saving slot to database: {e}")
        return None

# Helper function to update task status
def update_task_status(task_id, status=None, progress=None, current_venue=None, total_slots=None, error=None):
    """Update scraping task status in database"""
    try:
        task = ScrapingTask.query.filter_by(task_id=task_id).first()
        if task:
            if status:
                task.status = status
            if progress:
                task.progress = progress
            if current_venue:
                task.current_venue = current_venue
            if total_slots is not None:
                task.total_slots_found = total_slots
            if error:
                task.error = error
            if status in ['SUCCESS', 'FAILURE']:
                task.completed_at = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating task status: {e}")

# Helper function to run original scraper and save results to DB
def run_scraper_and_save_to_db(scraper_func, venue_name, city, guests, *args, task_id=None, **kwargs):
    """Run original scraper function and save results to database"""
    global scraped_data
    import logging
    import sys
    
    logger = logging.getLogger(__name__)
    
    # Force flush to ensure logs appear immediately
    print(f"[SCRAPER] Starting scraper for {venue_name} (city: {city}, guests: {guests})", flush=True)
    logger.info(f"[SCRAPER] Starting scraper for {venue_name} (city: {city}, guests: {guests})")
    sys.stdout.flush()
    sys.stderr.flush()
    
    print(f"[SCRAPER] About to call scraper function: {scraper_func.__name__}", flush=True)
    logger.info(f"[SCRAPER] About to call scraper function: {scraper_func.__name__}")
    
    # Initialize scraped_data if it doesn't exist (shouldn't happen, but safety check)
    try:
        _ = scraped_data
    except NameError:
        globals()['scraped_data'] = []
    
    # Clear scraped_data before running
    initial_length = len(scraped_data) if scraped_data else 0
    scraped_data = []
    
    # Run the original scraper (it will populate scraped_data)
    try:
        logger.info(f"[SCRAPER] Calling scraper function for {venue_name}...")
        scraper_func(*args, **kwargs)
        logger.info(f"[SCRAPER] Scraper function completed for {venue_name}")
    except Exception as e:
        logger.error(f"[SCRAPER] Error in scraper function for {venue_name}: {e}", exc_info=True)
        if task_id:
            update_task_status(task_id, status='FAILURE', error=str(e))
        raise e
    
    # Save all results to database
    slots_saved = 0
    new_items = scraped_data[initial_length:] if initial_length < len(scraped_data) else scraped_data
    
    logger.info(f"[SCRAPER] {venue_name}: Found {len(new_items)} items in scraped_data, saving to database...")
    
    for item in new_items:
        # Extract venue name from item or use provided
        item_venue_name = item.get('website', venue_name)
        
        # Determine city if not provided
        item_city = city
        if not item_city:
            if 'nyc' in item_venue_name.lower() or 'new york' in item_venue_name.lower():
                item_city = 'NYC'
            else:
                item_city = 'London'
        
        booking_url = item.get('booking_url') or VENUE_BOOKING_URLS.get(item_venue_name) or VENUE_BOOKING_URLS.get(venue_name)

        venue_specific = item.get('venue_specific_data') if isinstance(item.get('venue_specific_data'), dict) else item.get('venue_specific_data')

        saved = save_slot_to_db(
            venue_name=item_venue_name,
            date_str=item.get('date', ''),
            time=item.get('time', ''),
            price=item.get('price', ''),
            status=item.get('status', 'Available'),
            guests=guests,
            city=item_city,
            venue_specific_data=venue_specific,
            booking_url=booking_url
        )
        if saved:
            slots_saved += 1
    
    # Clear scraped_data after saving
    scraped_data = []
    
    logger.info(f"[SCRAPER] {venue_name}: Successfully saved {slots_saved} slots to database")
    
    return slots_saved


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


@celery_app.task(bind=True, name='app.scrape_swingers_task')
def scrape_swingers_task(self, guests, target_date, task_id=None):
    """Swingers scraper as Celery task - uses direct URL approach (updated from working test script)"""
    with app.app_context():
        try:
            # Update task status
            if task_id:
                task = ScrapingTask.query.filter_by(task_id=task_id).first()
                if task:
                    task.status = 'STARTED'
                    task.progress = 'Starting to scrape Swingers availability...'
                    db.session.commit()
            
            # Validate that target_date is provided
            if not target_date:
                raise ValueError("target_date is required for Swingers NYC scraper")
            
            # Parse the target date
            dt = datetime.strptime(target_date, "%Y-%m-%d")
            date_str = target_date
            month = dt.month
            year = dt.year
            day = dt.strftime("%d")
            month_abbr = dt.strftime("%b")
            
            # Build URL (matching test script)
            query_params = {
                "guests": str(guests),
                "search[month]": str(month),
                "search[year]": str(year),
                "depart": date_str
            }
            url = f"https://www.swingers.club/us/locations/nyc/book-now?{urlencode(query_params)}"
            
            if task_id:
                task = ScrapingTask.query.filter_by(task_id=task_id).first()
                if task:
                    task.progress = f'Loading Swingers availability page for {date_str}...'
                    task.current_venue = 'Swingers (NYC)'
                    db.session.commit()
            
            # Launch browser (matching test script config)
            driver = Driver(
                uc=False,
                headless2=False,
                no_sandbox=True,
                disable_gpu=True,
                headed=True,
            )
            
            driver.get(url)
            driver.sleep(5)
            
            slots_count = 0
            
            if task_id:
                task = ScrapingTask.query.filter_by(task_id=task_id).first()
                if task:
                    task.progress = f'Processing Swingers slots for {date_str}'
                    db.session.commit()
            
            # Parse HTML (matching test script)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            slots = soup.find_all("button", {"data-day": day, "data-month": month_abbr})
            
            for slot in slots:
                # Status
                status_el = slot.select_one("div.slot-search-result__low-stock")
                status = status_el.get_text(strip=True) if status_el else "Available"
                
                # Time
                try:
                    time_val = slot.find("span", {"class": "slot-search-result__time h5"}).get_text().strip()
                except:
                    time_val = "None"
                
                # Price
                try:
                    price_val = slot.find("span", {"class": "slot-search-result__price-label"}).get_text().strip()
                except:
                    price_val = "None"
                
                # Save to database
                save_slot_to_db(
                    venue_name='Swingers (NYC)',
                    date_str=date_str,
                    time=time_val,
                    price=price_val,
                    status=status,
                    guests=guests,
                    city='NYC',
                    booking_url=driver.current_url
                )
                slots_count += 1
                
                if task_id:
                    task = ScrapingTask.query.filter_by(task_id=task_id).first()
                    if task:
                        task.total_slots_found = slots_count
                        db.session.commit()
            
            driver.quit()
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_count} slots', total_slots=slots_count)
            
            return {'status': 'success', 'slots_found': slots_count}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


# Stub Celery tasks for other scrapers - these will be implemented similarly
# For now, they call original functions and save to DB
@celery_app.task(bind=True, name='app.scrape_swingers_uk_task')
def scrape_swingers_uk_task(self, guests, target_date, task_id=None):
    """Swingers UK scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Swingers UK...', current_venue='Swingers (London)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_swingers_uk,
                'Swingers (London)',
                'London',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_electric_shuffle_task')
def scrape_electric_shuffle_task(self, guests, target_date, task_id=None):
    """Electric Shuffle NYC scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Electric Shuffle NYC...', current_venue='Electric Shuffle (NYC)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_electric_shuffle,
                'Electric Shuffle (NYC)',
                'NYC',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_electric_shuffle_london_task')
def scrape_electric_shuffle_london_task(self, guests, target_date, task_id=None):
    """Electric Shuffle London scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Electric Shuffle London...', current_venue='Electric Shuffle (London)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_electric_shuffle_london,
                'Electric Shuffle (London)',
                'London',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_lawn_club_task')
def scrape_lawn_club_task(self, guests, target_date, option, task_id=None, selected_time=None, selected_duration=None):
    """Lawn Club scraper as Celery task"""
    with app.app_context():
        try:
            venue_name = f'Lawn Club NYC ({option})'
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_lawn_club,
                venue_name,
                'NYC',
                guests,
                guests,
                target_date,
                option,
                selected_time,
                selected_duration,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_spin_task')
def scrape_spin_task(self, guests, target_date, task_id=None, selected_time=None):
    """SPIN scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape SPIN NYC...', current_venue='SPIN (NYC)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_spin,
                'SPIN (NYC)',
                'NYC',
                guests,
                guests,
                target_date,
                selected_time,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_five_iron_golf_task')
def scrape_five_iron_golf_task(self, guests, target_date, task_id=None):
    """Five Iron Golf scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Five Iron Golf...', current_venue='Five Iron Golf (NYC)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_five_iron_golf,
                'Five Iron Golf (NYC)',
                'NYC',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_lucky_strike_task')
def scrape_lucky_strike_task(self, guests, target_date, task_id=None):
    """Lucky Strike scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Lucky Strike...', current_venue='Lucky Strike (NYC)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_lucky_strike,
                'Lucky Strike (NYC)',
                'NYC',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_easybowl_task')
def scrape_easybowl_task(self, guests, target_date, task_id=None):
    """Easybowl scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Easybowl...', current_venue='Easybowl (NYC)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_easybowl,
                'Easybowl (NYC)',
                'NYC',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_fair_game_canary_wharf_task')
def scrape_fair_game_canary_wharf_task(self, guests, target_date, task_id=None):
    """Fair Game Canary Wharf scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Fair Game (Canary Wharf)...', current_venue='Fair Game (Canary Wharf)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_fair_game_canary_wharf,
                'Fair Game (Canary Wharf)',
                'London',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_fair_game_city_task')
def scrape_fair_game_city_task(self, guests, target_date, task_id=None):
    """Fair Game City scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Fair Game (City)...', current_venue='Fair Game (City)')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_fair_game_city,
                'Fair Game (City)',
                'London',
                guests,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_clays_bar_task')
def scrape_clays_bar_task(self, location, guests, target_date, task_id=None):
    """Clays Bar scraper as Celery task"""
    with app.app_context():
        try:
            venue_name = f'Clays Bar ({location})'
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_clays_bar,
                venue_name,
                'London',
                guests,
                location,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_puttshack_task')
def scrape_puttshack_task(self, location, guests, target_date, task_id=None):
    """Puttshack scraper as Celery task"""
    with app.app_context():
        try:
            venue_name = f'Puttshack ({location})'
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_puttshack,
                venue_name,
                'London',
                guests,
                location,
                guests,
                target_date,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_flight_club_darts_task')
def scrape_flight_club_darts_task(self, guests, target_date, venue_id, task_id=None):
    """Flight Club Darts scraper as Celery task"""
    with app.app_context():
        try:
            venue_names = {
                "1": "Flight Club Darts",
                "2": "Flight Club Darts (Angel)",
                "3": "Flight Club Darts (Shoreditch)",
                "4": "Flight Club Darts (Victoria)"
            }
            venue_name = venue_names.get(venue_id, "Flight Club Darts")
            
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_flight_club_darts,
                venue_name,
                'London',
                guests,
                guests,
                target_date,
                venue_id,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_f1_arcade_task')
def scrape_f1_arcade_task(self, guests, target_date, f1_experience, task_id=None):
    """F1 Arcade scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape F1 Arcade...', current_venue='F1 Arcade')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_f1_arcade,
                'F1 Arcade',
                'London',
                guests,
                guests,
                target_date,
                f1_experience,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise


def scrape_swingers_uk(guests, target_date):
    """Swingers UK scraper function (updated from working test script)"""
    global scraping_status, scraped_data
    
    try:
        # Parse date (matching test script)
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        date_str = target_date
        month = dt.month
        year = dt.year
        day = dt.strftime("%d")
        month_abbr = dt.strftime("%b")
        
        # Build UK URL with full query params (matching test script)
        query_params = {
            "guests": str(guests),
            "search[month]": str(month),
            "search[year]": str(year),
            "depart": date_str
        }
        url = f"https://www.swingers.club/uk/book-now?{urlencode(query_params)}"
        
        scraping_status['progress'] = f'Loading Swingers UK availability page for {date_str}...'
        
        # Launch browser (matching test script config)
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )
        
        driver.get(url)
        driver.sleep(5)
        
        scraping_status['progress'] = f'Processing Swingers UK slots for {date_str}'
        scraping_status['current_date'] = date_str
        
        # Parse available dates (matching test script)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        dates = soup.find_all(
            "li",
            {"class": "slot-calendar__dates-item", "data-available": "true"}
        )
        
        if len(dates) == 0:
            scraping_status['progress'] = "No available dates found."
            driver.quit()
            return
        
        # Find the matching date in the calendar
        target_li = None
        for d in dates:
            if d.get("data-date") == target_date:
                target_li = d
                break
        
        if not target_li:
            scraping_status['progress'] = f"No calendar entry found for {target_date}"
            driver.quit()
            return
        
        # Navigate to the date page
        full_url = "https://www.swingers.club" + target_li.find("a")["href"]
        driver.get(full_url)
        driver.sleep(5)
        
        # Parse slots (matching test script)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        slots = soup.find_all("button", {"data-day": day, "data-month": month_abbr})
        
        for slot in slots:
            # Status
            status_el = slot.select_one("div.slot-search-result__low-stock")
            status = status_el.get_text(strip=True) if status_el else "Available"
            
            # Time
            try:
                time_val = slot.find("span", {"class": "slot-search-result__time h5"}).get_text(strip=True)
            except:
                time_val = "None"
            
            # Price
            try:
                price_val = slot.find("span", {"class": "slot-search-result__price-label"}).get_text(strip=True)
            except:
                price_val = "None"
            
            # Store data in memory
            slot_data = {
                "date": target_date,
                "time": time_val,
                "price": price_val,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "website": "Swingers (London)"
            }
            
            scraped_data.append(slot_data)
            scraping_status['total_slots_found'] = len(scraped_data)
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_electric_shuffle(guests, target_date):
    """Electric Shuffle NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )
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
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_electric_shuffle_london(guests, target_date):
    """Electric Shuffle London scraper function (updated from working test script)"""
    global scraping_status, scraped_data

    try:
        # Build URL (matching test script)
        url = (
            "https://electricshuffle.com/uk/london/book/shuffleboard?"
            f"preferedvenue=7&preferedtime=23%3A00&guestQuantity={guests}&date={target_date}"
        )

        scraping_status['progress'] = f'Scraping Electric Shuffle London for {target_date}...'
        scraping_status['current_date'] = target_date

        # Driver (matching test script config)
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )

        # Load page
        driver.get(url)
        driver.sleep(3)

        # WAIT FOR JS TO LOAD SLOTS (matching test script)
        max_wait = 30
        interval = 0.5
        elapsed = 0
        loaded = False

        while elapsed < max_wait:
            soup = BeautifulSoup(driver.page_source, "html.parser")

            loading_msg = soup.select_one(".es_booking__availability__message")
            slots_exist = soup.select_one("div.es_booking__availability__table-cell__wrapper")

            if slots_exist:
                loaded = True
                break

            if loading_msg:
                txt = loading_msg.get_text(strip=True)
                if "Loading" not in txt:
                    loaded = True
                    break

            driver.sleep(interval)
            elapsed += interval

        if not loaded:
            scraping_status['progress'] = "Timeout: No slots loaded"
            driver.quit()
            return

        # PARSE THE PAGE (matching test script)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        holders = soup.select("form.es_booking__availability__form")

        if not holders:
            scraping_status['progress'] = "No venue sections found"
            driver.quit()
            return

        scraping_status['progress'] = f"Found {len(holders)} venue sections"

        # Loop through venue sections
        for holder in holders:
            # Venue title
            title = holder.select_one(
                "div.es_booking__availability-header.es_font-body--semi-bold"
            )
            venue_name = title.get_text(strip=True) if title else "Unknown Venue"

            # Slots inside that venue
            slots = holder.select("div.es_booking__availability__table-cell__wrapper")

            for slot in slots:
                # Extract time
                try:
                    time_val = slot.select_one(
                        "div.es_booking__availability__table-cell"
                    )["name"]
                except:
                    time_val = "None"

                # Extract content inside wrapper
                wrap = slot.select_one("div.es_booking__time_wrapper")
                desc_parts = []

                if wrap:
                    inputs = wrap.select("input.es_booking__availability__time-slot")

                    for inp in inputs:
                        label = inp.find_next("label")

                        # Duration
                        dur_el = label.select_one(".es_booking__availability__duration")
                        duration = dur_el.get_text(strip=True) if dur_el else None
                        if duration:
                            duration = duration.replace("mins", "min")

                        # Price
                        price_el = label.select_one(".es_booking__availability__price-per-person")
                        price = price_el.get_text(strip=True) if price_el else None

                        if inp.has_attr("disabled"):
                            desc_parts.append("unavailable")
                        else:
                            if duration and price:
                                desc_parts.append(f"{duration} {price}")
                            elif duration:
                                desc_parts.append(duration)
                            else:
                                desc_parts.append("available")

                desc = ", ".join(desc_parts) if desc_parts else "unavailable"

                slot_data = {
                    "date": target_date,
                    "time": time_val,
                    "price": f"{venue_name} - {desc}",
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": "Electric Shuffle (London)"
                }

                scraped_data.append(slot_data)
                scraping_status["total_slots_found"] = len(scraped_data)

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
        driver = Driver(        
            uc=False,        
            headless2=False, # server-safe true headless        
            no_sandbox=True,        
            disable_gpu=True,        
            headed=True,        
        )
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
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_spin(guests, target_date, selected_time=None):
    """SPIN NYC scraper function"""
    global scraping_status, scraped_data
    
    try:
        import platform
        import logging
        logger = logging.getLogger(__name__)
        
        date_str = target_date
        
        # On Linux, try headless=True first as headless2 might not work properly
        if platform.system() == 'Linux':
            driver_kwargs = {'headless': True, 'no_sandbox': True, 'disable_gpu': True}
        else:
            driver_kwargs = {'headless2': True, 'no_sandbox': True, 'disable_gpu': True}
        
        logger.info("[SCRAPER] Creating Chrome driver for SPIN...")
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )
        logger.info("[SCRAPER] Driver created successfully")
        
        # On Linux, wait a moment for Chrome to fully initialize before navigation
        if platform.system() == 'Linux':
            import time
            logger.info("[SCRAPER] Waiting for Chrome to initialize on Linux...")
            time.sleep(1)
        
        # Set page load timeout to prevent hanging
        driver.set_page_load_timeout(30)
        logger.info("[SCRAPER] Navigating to SPIN NYC...")
        
        try:
            driver.get("https://wearespin.com/location/new-york-flatiron/table-reservations/#elementor-action%3Aaction%3Doff_canvas%3Aopen%26settings%3DeyJpZCI6ImM4OGU1Y2EiLCJkaXNwbGF5TW9kZSI6Im9wZW4ifQ%3D%3D")
            logger.info("[SCRAPER] Page loaded successfully")
        except Exception as e:
            logger.error(f"[SCRAPER] Page load failed: {str(e)}")
            scraping_status['progress'] = f'Page load timeout or error: {str(e)}'
            if 'driver' in locals():
                driver.quit()
            raise
        
        scraping_status['progress'] = f'Navigating to SPIN NYC reservation system...'
        scraping_status['current_date'] = target_date
        
        # Close Elementor popup modal if present
        try:
            driver.sleep(2)  # Wait for popup to appear
            driver.execute_script("""
                var modals = document.querySelectorAll('.elementor-popup-modal');
                modals.forEach(function(modal) {
                    var closeBtn = modal.querySelector('.elementor-popup-modal-close, button[aria-label="Close"], [class*="close"]');
                    if (closeBtn) {
                        closeBtn.click();
                    } else {
                        modal.style.display = 'none';
                    }
                });
            """)
            driver.sleep(1)
        except:
            pass  # No popup, continue
        
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
        
        driver = Driver(        
            uc=False,        
            headless2=False, # server-safe true headless        
            no_sandbox=True,        
            disable_gpu=True,        
            headed=True,        
        )
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
        
        # Try to create driver with uc=True, fallback to regular Chrome if binary not found
        import platform
        import logging
        logger = logging.getLogger(__name__)
        
        # On Linux, try headless=True first as headless2 might not work properly
        if platform.system() == 'Linux':
            driver_kwargs = {'headless': True, 'no_sandbox': True, 'disable_gpu': True}
        else:
            driver_kwargs = {'headless2': True, 'no_sandbox': True, 'disable_gpu': True}
        
        logger.info("[SCRAPER] Creating Chrome driver for Lucky Strike...")
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )
        logger.info("[SCRAPER] Driver created successfully")
        
        # On Linux, wait a moment for Chrome to fully initialize before navigation
        if platform.system() == 'Linux':
            import time
            logger.info("[SCRAPER] Waiting for Chrome to initialize on Linux...")
            time.sleep(1)
        
        # Set page load timeout to prevent hanging
        driver.set_page_load_timeout(30)
        logger.info(f"[SCRAPER] Navigating to Lucky Strike: {url}")
        
        try:
            driver.get(url)
            logger.info("[SCRAPER] Page loaded successfully")
        except Exception as e:
            logger.error(f"[SCRAPER] Page load failed: {str(e)}")
            scraping_status['progress'] = f'Page load timeout or error: {str(e)}'
            if 'driver' in locals():
                driver.quit()
            raise
        
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
        driver = Driver(        
            uc=False,        
            headless2=False, # server-safe true headless        
            no_sandbox=True,        
            disable_gpu=True,        
            headed=True,        
        )
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
        driver = Driver(        
            uc=False,        
            headless2=False, # server-safe true headless        
            no_sandbox=True,        
            disable_gpu=True,        
            headed=True,        
        )
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
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_fair_game_city(guests, target_date):
    """Fair Game City (London) scraper function"""
    global scraping_status, scraped_data
    
    import platform
    import logging
    import sys
    logger = logging.getLogger(__name__)
    
    try:
        # On Linux, skip uc=True entirely as it causes hanging
        if platform.system() == 'Linux':
            print("[SCRAPER] On Linux - skipping uc=True to avoid hanging", flush=True)
            logger.info("[SCRAPER] On Linux - skipping uc=True to avoid hanging")
            driver_kwargs = {'headless': True, 'no_sandbox': True, 'disable_gpu': True}
            use_uc = False
        else:
            driver_kwargs = {'headless2': True, 'no_sandbox': True, 'disable_gpu': True}
            use_uc = True
        
        print(f"[SCRAPER] Creating Chrome driver for Fair Game City...", flush=True)
        logger.info(f"[SCRAPER] Creating Chrome driver for Fair Game City...")
        
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )
        
        print("[SCRAPER] Driver created successfully!", flush=True)
        logger.info("[SCRAPER] Driver created successfully")
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        print(f"[SCRAPER] Navigating to Fair Game City...", flush=True)
        
        try:
            driver.get(f"https://www.sevenrooms.com/explore/fairgamecity/reservations/create/search/?date={target_date}&party_size={guests}")
            print("[SCRAPER] Page loaded successfully!", flush=True)
        except Exception as e:
            print(f"[SCRAPER] Page load failed: {str(e)}", flush=True)
            logger.error(f"[SCRAPER] Page load failed: {str(e)}")
            if 'driver' in locals():
                driver.quit()
            raise
        
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
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


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
        driver = Driver(        
            uc=False,        
            headless2=False, # server-safe true headless        
            no_sandbox=True,        
            disable_gpu=True,        
            headed=True,        
        )
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

        driver.quit()

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_puttshack(location, guests, target_date):
    """Puttshack (London) scraper function"""
    global scraping_status, scraped_data
    
    try:
        driver = Driver(        
            uc=False,        
            headless2=False, # server-safe true headless        
            no_sandbox=True,        
            disable_gpu=True,        
            headed=True,        
        )
        driver.get("https://www.puttshack.com/book-golf")
        
        scraping_status['progress'] = f'Navigating to Puttshack {location}...'
        scraping_status['current_date'] = target_date
        
        driver.sleep(4)
        
        # Close GetSiteControl widget if present
        try:
            driver.execute_script("""
                var widget = document.getElementById('getsitecontrol-518774');
                if (widget) {
                    widget.style.display = 'none';
                    widget.remove();
                }
                var allWidgets = document.querySelectorAll('getsitecontrol-widget');
                allWidgets.forEach(function(w) { w.style.display = 'none'; w.remove(); });
            """)
            driver.sleep(0.5)
        except:
            pass  # Continue if script fails
        
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
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_flight_club_darts(guests, target_date, venue_id="1"):
    """Flight Club Darts (London) scraper function with venue selection (updated from working test script)"""
    global scraping_status, scraped_data
    
    try:
        # Venue mapping (matching test script)
        venue_names = {
            "1": "Flight Club Darts",
            "2": "Flight Club Darts (Angel)",
            "3": "Flight Club Darts (Shoreditch)",
            "4": "Flight Club Darts (Victoria)"
        }
        venue_name = venue_names.get(venue_id, "Flight Club Darts")
        
        # Map venue_id to expected holder_title (location name from the page)
        holder_title_map = {
            "1": "Bloomsbury, London",
            "2": "Angel, London",
            "3": "Shoreditch, London",
            "4": "Victoria, London"
        }
        expected_holder_title = holder_title_map.get(venue_id, "Bloomsbury, London")
        
        scraping_status['progress'] = f'Scraping {venue_name} for {target_date}...'
        scraping_status['current_date'] = target_date
        
        # Build URL (matching test script)
        url = (
            f"https://flightclubdarts.com/book?"
            f"date={target_date}&group_size={guests}&preferedtime=11%3A30&preferedvenue={venue_id}"
        )
        
        # Launch browser (matching test script config)
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )
        
        driver.get(url)
        driver.sleep(30)
        
        # Parse Page (matching test script)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        holders = soup.select("div.fc_dmnbook-availability")
        
        if not holders:
            scraping_status['progress'] = "No slots found."
            driver.quit()
            return
        
        scraping_status['progress'] = f'Found {len(holders)} venue sections, filtering for {expected_holder_title}'
        
        # Loop through venue sections and filter by holder_title
        slots_found = 0
        for holder in holders:
            try:
                title_el = holder.find("span", {"id": "fc_dmnbook-availability__name"})
                holder_title = title_el.get_text(strip=True) if title_el else "Unknown Venue"
            except:
                holder_title = "Unknown Venue"
            
            # Only process slots from the matching holder_title
            if holder_title != expected_holder_title:
                continue  # Skip holders that don't match the expected location
            
            slots = holder.find_all("div", {"class": "fc_dmnbook-availability-tablecell tns-item"})
            
            for slot in slots:
                # Time
                try:
                    time_val = slot.find(
                        "div", {"class": "fc_dmnbook-availibility__time font-small"}
                    ).get_text(strip=True)
                except:
                    time_val = "None"
                
                # Description
                try:
                    desc = slot.find(
                        "div", {"class": "fc_dmnbook-time_wrapper"}
                    ).get_text(strip=True).replace("\n", "")
                except:
                    desc = "None"
                
                slot_data = {
                    "date": target_date,
                    "time": time_val,
                    "price": f"{holder_title} - {desc}",
                    "status": "Available",
                    "timestamp": datetime.now().isoformat(),
                    "website": venue_name
                }
                
                scraped_data.append(slot_data)
                slots_found += 1
                scraping_status['total_slots_found'] = len(scraped_data)
        
        scraping_status['progress'] = f'Found {slots_found} slots for {venue_name} ({expected_holder_title})'
        
        driver.quit()
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e


def scrape_f1_arcade(guests, target_date, f1_experience):
    """F1 Arcade (London) scraper function - UPDATED from old version"""
    global scraping_status, scraped_data

    try:
        import platform
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[SCRAPER] Creating Chrome driver for F1 Arcade...")
        print(f"[SCRAPER] Creating Chrome driver for F1 Arcade...", flush=True)
        
        driver = Driver(
            uc=False,
            headless2=False,
            no_sandbox=True,
            disable_gpu=True,
            headed=True,
        )
        print("[SCRAPER] Driver created successfully!", flush=True)
        logger.info("[SCRAPER] Driver created successfully")
        
        driver.sleep(10)

        # On Linux, wait a moment for Chrome to fully initialize before navigation
        if platform.system() == 'Linux':
            import time
            logger.info("[SCRAPER] Waiting for Chrome to initialize on Linux...")
            time.sleep(1)
        
        # Set page load timeout to prevent hanging
        driver.set_page_load_timeout(30)
        logger.info("[SCRAPER] Navigating to F1 Arcade...")
        
        try:
            driver.get("https://f1arcade.com/uk/booking/venue/london")
            logger.info("[SCRAPER] Page loaded successfully")
        except Exception as e:
            logger.error(f"[SCRAPER] Page load failed: {str(e)}")
            scraping_status['progress'] = f'Page load timeout or error: {str(e)}'
            if 'driver' in locals():
                driver.quit()
            raise

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
        # 2️⃣ SELECT EXPERIENCE
        # ----------------------------------------
        scraping_status['progress'] = f"Selecting experience: {f1_experience}"
        xp_map = {
            "Team Racing": "//h2[contains(text(),'Team Racing')]",
            "Christmas Racing": "//h2[contains(text(),'Christmas Racing')]",
            "Head to Head": "//h2[contains(text(),'Head to Head')]"
        }

        xp = xp_map.get(f1_experience)

        if xp:
            try:
                exp_el = driver.find_element("xpath", xp)
                driver.execute_script("arguments[0].scrollIntoView(true);", exp_el)
                driver.sleep(1)
                driver.execute_script("arguments[0].click();", exp_el)
            except:
                scraping_status['progress'] = f"Could not click {f1_experience}"

        driver.sleep(2)

        # ----------------------------------------
        # 3️⃣ CLICK CONTINUE
        # ----------------------------------------
        scraping_status['progress'] = "Clicking Continue..."
        try:
            cont = driver.find_element("id", "game-continue")
            driver.execute_script("arguments[0].click();", cont)
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

        # Reset backward
        for _ in range(6):
            try:
                prev = driver.find_element("id", "prev-month-btn")
                driver.execute_script("arguments[0].click();", prev)
                driver.sleep(0.2)
            except:
                break

        # Forward until month matches
        while True:
            header = driver.find_element("xpath", "//div[@id='date-picker']//h2").text.strip()
            if header == target_month:
                break
            next_btn = driver.find_element("id", "next-month-btn")
            driver.execute_script("arguments[0].click();", next_btn)
            driver.sleep(0.3)

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
            scraping_status['progress'] = f"Day {day} unavailable"
            driver.quit()
            return

        driver.sleep(13)

        # ========================================
        # ⭐️ UPDATED PRICE + SLOT EXTRACTION ⭐️
        # ========================================
        scraping_status['progress'] = "Extracting pricing & slot details..."

        soup = BeautifulSoup(driver.page_source, "html.parser")
        # --------- PRICE HEADER EXTRACTION ----------
        price_headers = soup.select(".flex.grow.justify-center")
        price_map = {}   # {"Offpeak": "19.95", "Standard": "22.95", "Peak": "24.95"}

        for block in price_headers:
            label_div = block.find("div", class_="-mt-1")
            if not label_div:
                continue

            label = label_div.find("div").get_text(strip=True)
            price_div = label_div.find("div", class_="text-xxs")

            if price_div:
                price_value = price_div.get_text(strip=True).replace("from £", "")
                price_map[label] = price_value  # e.g. "Offpeak": "19.95"

        # -------------------------------------------
        # TIME SLOT EXTRACTION WITH COLOR-BASED PRICE
        # -------------------------------------------
        slot_divs = soup.find_all("div", {"data-target": "time-picker-option"})

        COLOR_PRICE_CLASS = {
            "bg-light-grey": "Offpeak",
            "bg-electric-violet-light": "Standard",
            "bg-brand-primary": "Peak"
        }

        for slot in slot_divs:
            time_text = slot.get_text(strip=True)

            # Find class of inner DIV (contains bg-color)
            inner = slot.find("div", class_="animate")
            if not inner:
                continue

            box = inner.find("div")  # the actual colored box
            if not box:
                continue

            classes = box.get("class", [])

            price_type = None
            for c in classes:
                if c in COLOR_PRICE_CLASS:
                    price_type = COLOR_PRICE_CLASS[c]
                    break

            if not price_type:
                price_type = "Unknown"

            final_price = f"{price_type} from £{price_map.get(price_type, 'N/A')}"

            scraped_data.append({
                "date": target_date,
                "time": time_text,
                "price": final_price,
                "status": "Available",
                "timestamp": datetime.now().isoformat(),
                "website": "F1 Arcade"
            })

            scraping_status['total_slots_found'] = len(scraped_data)


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

            scraped_data.append({
                "date": target_date,
                "time": time_text,
                "price": final_price,
                "status": "Available",
                "timestamp": datetime.now().isoformat(),
                "website": "F1 Arcade"
            })

            scraping_status['total_slots_found'] = len(scraped_data)

        driver.quit()

    except Exception as e:
        if "driver" in locals():
            driver.quit()
        raise e

@celery_app.task(bind=True, name='app.scrape_venue_task')
def scrape_venue_task(self, guests, target_date, website, task_id=None, lawn_club_option=None, lawn_club_time=None, lawn_club_duration=None, spin_time=None, clays_location=None, puttshack_location=None, f1_experience=None):
    """Celery task wrapper for scraping a single venue"""
    with app.app_context():
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"[VENUE_TASK] Starting scrape for {website} (date: {target_date}, guests: {guests})")
            
            # Create or update task status
            if task_id:
                task = ScrapingTask.query.filter_by(task_id=task_id).first()
                if not task:
                    task = ScrapingTask(
                        task_id=task_id,
                        website=website,
                        guests=guests,
                        target_date=datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else None,
                        status='STARTED',
                        progress='Initializing browser...'
                    )
                    db.session.add(task)
                else:
                    task.status = 'STARTED'
                    task.progress = 'Initializing browser...'
                db.session.commit()
            
            # Temporary list to collect results
            temp_results = []
            
            # Determine city and venue name
            city = 'NYC' if 'nyc' in website or website in NYC_VENUES else 'London'
            venue_name_map = {
                'swingers_nyc': 'Swingers (NYC)',
                'swingers_london': 'Swingers (London)',
                'electric_shuffle_nyc': 'Electric Shuffle (NYC)',
                'electric_shuffle_london': 'Electric Shuffle (London)',
                'lawn_club_nyc': 'Lawn Club NYC',
                'spin_nyc': 'SPIN (NYC)',
                'five_iron_golf_nyc': 'Five Iron Golf (NYC)',
                'lucky_strike_nyc': 'Lucky Strike (NYC)',
                'easybowl_nyc': 'Easybowl (NYC)',
                'fair_game_canary_wharf': 'Fair Game (Canary Wharf)',
                'fair_game_city': 'Fair Game (City)',
                'clays_bar': f'Clays Bar ({clays_location or "Canary Wharf"})',
                'puttshack': f'Puttshack ({puttshack_location or "Bank"})',
                'flight_club_darts': 'Flight Club Darts',
                'flight_club_darts_angel': 'Flight Club Darts (Angel)',
                'flight_club_darts_shoreditch': 'Flight Club Darts (Shoreditch)',
                'flight_club_darts_victoria': 'Flight Club Darts (Victoria)',
                'f1_arcade': 'F1 Arcade'
            }
            venue_name = venue_name_map.get(website, website.replace('_', ' ').title())
            
            # Call appropriate scraper (using original functions but intercepting results)
            # We'll modify the approach to call scrapers and save to DB directly
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[VENUE_TASK] {website} ({venue_name}): Calling scraper task function for date {target_date} with {guests} guests...")
            
            if website == 'swingers_nyc':
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_swingers_task")
                result = scrape_swingers_task(guests, target_date, task_id)
            elif website == 'swingers_london':
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_swingers_uk_task")
                result = scrape_swingers_uk_task(guests, target_date, task_id)
            elif website == 'electric_shuffle_nyc':
                if not target_date:
                    raise ValueError("Electric Shuffle NYC requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_electric_shuffle_task")
                result = scrape_electric_shuffle_task(guests, target_date, task_id)
            elif website == 'electric_shuffle_london':
                if not target_date:
                    raise ValueError("Electric Shuffle London requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_electric_shuffle_london_task")
                result = scrape_electric_shuffle_london_task(guests, target_date, task_id)
            elif website == 'lawn_club_nyc':
                if not target_date:
                    raise ValueError("Lawn Club NYC requires a specific target date")
                option = lawn_club_option or "Curling Lawns & Cabins"
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_lawn_club_task with option {option}")
                venue_specific = {'lawn_club_option': option, 'lawn_club_time': lawn_club_time, 'lawn_club_duration': lawn_club_duration}
                result = scrape_lawn_club_task(guests, target_date, option, task_id, lawn_club_time, lawn_club_duration)
            elif website == 'spin_nyc':
                if not target_date:
                    raise ValueError("SPIN NYC requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_spin_task")
                result = scrape_spin_task(guests, target_date, task_id, spin_time)
            elif website == 'five_iron_golf_nyc':
                if not target_date:
                    raise ValueError("Five Iron Golf NYC requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_five_iron_golf_task")
                result = scrape_five_iron_golf_task(guests, target_date, task_id)
            elif website == 'lucky_strike_nyc':
                if not target_date:
                    raise ValueError("Lucky Strike NYC requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_lucky_strike_task")
                result = scrape_lucky_strike_task(guests, target_date, task_id)
            elif website == 'easybowl_nyc':
                if not target_date:
                    raise ValueError("Easybowl NYC requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_easybowl_task")
                result = scrape_easybowl_task(guests, target_date, task_id)
            elif website == 'fair_game_canary_wharf':
                if not target_date:
                    raise ValueError("Fair Game (Canary Wharf) requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_fair_game_canary_wharf_task")
                result = scrape_fair_game_canary_wharf_task(guests, target_date, task_id)
            elif website == 'fair_game_city':
                if not target_date:
                    raise ValueError("Fair Game (City) requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_fair_game_city_task")
                result = scrape_fair_game_city_task(guests, target_date, task_id)
            elif website == 'clays_bar':
                if not target_date:
                    raise ValueError("Clays Bar requires a specific target date")
                location = clays_location or "Canary Wharf"
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_clays_bar_task with location {location}")
                result = scrape_clays_bar_task(location, guests, target_date, task_id)
            elif website == 'puttshack':
                if not target_date:
                    raise ValueError("Puttshack requires a specific target date")
                location = puttshack_location or "Bank"
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_puttshack_task with location {location}")
                result = scrape_puttshack_task(location, guests, target_date, task_id)
            elif website == 'flight_club_darts':
                if not target_date:
                    raise ValueError("Flight Club Darts requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_flight_club_darts_task with venue_id 1")
                result = scrape_flight_club_darts_task(guests, target_date, "1", task_id)
            elif website == 'flight_club_darts_angel':
                if not target_date:
                    raise ValueError("Flight Club Darts (Angel) requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_flight_club_darts_task with venue_id 2")
                result = scrape_flight_club_darts_task(guests, target_date, "2", task_id)
            elif website == 'flight_club_darts_shoreditch':
                if not target_date:
                    raise ValueError("Flight Club Darts (Shoreditch) requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_flight_club_darts_task with venue_id 3")
                result = scrape_flight_club_darts_task(guests, target_date, "3", task_id)
            elif website == 'flight_club_darts_victoria':
                if not target_date:
                    raise ValueError("Flight Club Darts (Victoria) requires a specific target date")
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_flight_club_darts_task with venue_id 4")
                result = scrape_flight_club_darts_task(guests, target_date, "4", task_id)
            elif website == 'f1_arcade':
                if not target_date:
                    raise ValueError("F1 Arcade requires a specific target date")
                experience = f1_experience or "Team Racing"
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_f1_arcade_task with experience {experience}")
                result = scrape_f1_arcade_task(guests, target_date, experience, task_id)
            else:
                logger.error(f"[VENUE_TASK] {website}: Unknown website!")
                raise ValueError(f"Unknown website: {website}")
            
            slots_found = result.get("slots_found", 0) if isinstance(result, dict) else 0
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[VENUE_TASK] {website}: Completed scraping, found {slots_found} slots")
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Scraping completed! Found {slots_found} slots')
            
            return result
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[VENUE_TASK] {website}: Error during scraping: {e}", exc_info=True)
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.refresh_all_venues_task')
def refresh_all_venues_task(self):
    """Periodic task to refresh all venues for 30 days from today, split into smaller chunks"""
    with app.app_context():
        try:
            from datetime import date, timedelta
            import logging
            logger = logging.getLogger(__name__)
            
            # Refresh for 30 days from today
            today = date.today()
            dates_to_refresh = [today + timedelta(days=i) for i in range(30)]  # 30 days from today
            
            guests = 6  # Default guest count
            
            # Split 30 days into smaller chunks for better performance
            # 6 chunks of 5 days each = 12 tasks total (6 for NYC, 6 for London)
            days_per_chunk = 5
            num_chunks = (len(dates_to_refresh) + days_per_chunk - 1) // days_per_chunk  # Ceiling division
            
            logger.info(f"[REFRESH] Starting refresh for {len(dates_to_refresh)} dates (30 days from today)")
            logger.info(f"[REFRESH] Date range: {dates_to_refresh[0]} to {dates_to_refresh[-1]}")
            logger.info(f"[REFRESH] Splitting into {num_chunks} chunks of ~{days_per_chunk} days each")
            logger.info(f"[REFRESH] NYC venues: {NYC_VENUES}")
            logger.info(f"[REFRESH] London venues: {LONDON_VENUES}")
            
            tasks_created = 0
            
            # Schedule tasks for NYC in chunks
            for chunk_idx in range(num_chunks):
                start_idx = chunk_idx * days_per_chunk
                end_idx = min(start_idx + days_per_chunk, len(dates_to_refresh))
                chunk_dates = dates_to_refresh[start_idx:end_idx]
                date_strings = [d.isoformat() for d in chunk_dates]
                
                logger.info(f"[REFRESH] Scheduling NYC venues for chunk {chunk_idx + 1}/{num_chunks} ({len(chunk_dates)} dates: {chunk_dates[0]} to {chunk_dates[-1]})")
                scrape_all_venues_task.delay('NYC', guests, date_strings, None, None)
                tasks_created += 1
            
            # Schedule tasks for London in chunks
            for chunk_idx in range(num_chunks):
                start_idx = chunk_idx * days_per_chunk
                end_idx = min(start_idx + days_per_chunk, len(dates_to_refresh))
                chunk_dates = dates_to_refresh[start_idx:end_idx]
                date_strings = [d.isoformat() for d in chunk_dates]
                
                logger.info(f"[REFRESH] Scheduling London venues for chunk {chunk_idx + 1}/{num_chunks} ({len(chunk_dates)} dates: {chunk_dates[0]} to {chunk_dates[-1]})")
                scrape_all_venues_task.delay('London', guests, date_strings, None, None)
                tasks_created += 1
            
            logger.info(f"[REFRESH] All refresh tasks scheduled successfully ({tasks_created} tasks total)")
            return {'status': 'success', 'dates_refreshed': len(dates_to_refresh), 'tasks_created': tasks_created, 'chunks': num_chunks}
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[REFRESH] Error in refresh_all_venues_task: {e}", exc_info=True)
            raise e


@celery_app.task(bind=True, name='app.scrape_all_venues_task')
def scrape_all_venues_task(self, city, guests, target_date, task_id=None, options=None):
    """Scrape all venues in a city for one or more dates simultaneously using Celery group"""
    with app.app_context():
        import time
        import uuid
        start_time = time.time()  # Record start time
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Handle both single date (string) and multiple dates (list)
            if isinstance(target_date, str):
                target_dates = [target_date]
            elif isinstance(target_date, list):
                target_dates = target_date
            else:
                raise ValueError(f"target_date must be a string or list, got {type(target_date)}")
            
            # Use Celery task ID if no task_id provided (for periodic tasks)
            if not task_id:
                task_id = self.request.id
            
            # Get or create task record
            task = ScrapingTask.query.filter_by(task_id=task_id).first()
            if not task:
                # Create new task record for periodic scraping
                from datetime import date
                city_lower = city.lower()
                today = date.today()
                
                # For multiple dates, use a generic name
                if len(target_dates) == 1:
                    target_date_obj = datetime.strptime(target_dates[0], "%Y-%m-%d").date()
                    if target_date_obj == today:
                        date_type = 'today'
                    elif target_date_obj == today + timedelta(days=1):
                        date_type = 'tomorrow'
                    else:
                        date_type = target_date_obj.isoformat()
                else:
                    # Multiple dates - use a range identifier
                    first_date = datetime.strptime(target_dates[0], "%Y-%m-%d").date()
                    last_date = datetime.strptime(target_dates[-1], "%Y-%m-%d").date()
                    date_type = f'{len(target_dates)}days_{first_date.isoformat()}_{last_date.isoformat()}'
                
                # Create website name
                if city_lower in ['nyc', 'new york']:
                    website_name = f'all_nyc_{date_type}'
                elif city_lower == 'london':
                    website_name = f'all_london_{date_type}'
                else:
                    website_name = f'all_{city_lower.replace(" ", "_")}_{date_type}'
                
                logger.info(f"[SCRAPE_ALL] Creating task record: website={website_name}, city={city}, dates={len(target_dates)}, task_id={task_id}")
                task = ScrapingTask(
                    task_id=task_id,
                    website=website_name,
                    guests=guests,
                    target_date=datetime.strptime(target_dates[0], "%Y-%m-%d").date() if target_dates else None,
                    status='STARTED',
                    progress=f'Starting to scrape all {city} venues for {len(target_dates)} date(s)...'
                )
                db.session.add(task)
                db.session.commit()
                logger.info(f"[SCRAPE_ALL] ✅ Task record created: {website_name} (task_id: {task_id})")
            else:
                task.status = 'STARTED'
                task.progress = f'Starting to scrape all {city} venues for {len(target_dates)} date(s)...'
                db.session.commit()
                logger.info(f"[SCRAPE_ALL] Using existing task record: {task.website} (task_id: {task_id})")
            
            # Get venue list based on city
            if city.lower() == 'nyc' or city.lower() == 'new york':
                venues = NYC_VENUES
                city_name = 'NYC'
            elif city.lower() == 'london':
                venues = LONDON_VENUES
                city_name = 'London'
            else:
                raise ValueError(f"Unknown city: {city}")
            
            logger.info(f"[SCRAPE_ALL] Starting to scrape {len(venues)} {city_name} venues for {len(target_dates)} date(s) with {guests} guests")
            logger.info(f"[SCRAPE_ALL] Dates: {target_dates[0]} to {target_dates[-1]}")
            logger.info(f"[SCRAPE_ALL] Venues: {venues}")
            
            options = options or {}
            
            # Create subtasks for each venue and date combination
            venue_tasks = []
            for venue in venues:
                for date_str in target_dates:
                    # Create a subtask for each venue-date combination
                    venue_task_id = f"{task_id}_{venue}_{date_str}" if task_id else None
                    logger.info(f"[SCRAPE_ALL] Creating task for venue: {venue}, date: {date_str}")
                    venue_tasks.append(
                        scrape_venue_task.s(
                            guests=guests,
                            target_date=date_str,
                            website=venue,
                            task_id=venue_task_id,
                            lawn_club_option=options.get('lawn_club_option'),
                            lawn_club_time=options.get('lawn_club_time'),
                            lawn_club_duration=options.get('lawn_club_duration'),
                            spin_time=options.get('spin_time'),
                            clays_location=options.get('clays_location'),
                            puttshack_location=options.get('puttshack_location'),
                            f1_experience=options.get('f1_experience')
                        )
                    )
            
            # Execute all tasks in parallel using group
            # Note: We don't wait for results synchronously (Celery doesn't allow result.get() within a task)
            # Instead, all individual venue tasks save their results directly to the database
            job = group(venue_tasks)
            result = job.apply_async()
            
            logger.info(f"[SCRAPE_ALL] All {len(venue_tasks)} venue-date tasks submitted to queue")
            logger.info(f"[SCRAPE_ALL] Tasks will execute in parallel and save results to database independently")
            
            # Don't wait for results - individual tasks save to DB
            # The parent task completes immediately after submitting child tasks
            venue_results = {}
            total_slots = 0  # Will be calculated from DB later if needed
            
            # Calculate duration
            end_time = time.time()
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60
            
            logger.info(f"[SCRAPE_ALL] Submitted {len(venue_tasks)} scraping tasks for {city_name} venues across {len(target_dates)} date(s)")
            logger.info(f"[SCRAPE_ALL] ⏱️  Task submission duration: {duration_seconds:.2f} seconds ({duration_minutes:.2f} minutes)")
            logger.info(f"[SCRAPE_ALL] Individual venue tasks are now running in parallel and saving results to database")
            
            # Mark task as submitted (not completed - child tasks are still running)
            task = ScrapingTask.query.filter_by(task_id=task_id).first()
            if task:
                task.status = 'SUBMITTED'
                task.progress = f'Submitted {len(venue_tasks)} scraping tasks for {len(venues)} {city_name} venues across {len(target_dates)} dates. Tasks are running in parallel.'
                # Don't set completed_at or duration_seconds yet - child tasks are still running
                db.session.commit()
                logger.info(f"[SCRAPE_ALL] ✅ Task marked as SUBMITTED: {task.website} (task_id: {task_id})")
            else:
                logger.error(f"[SCRAPE_ALL] ❌ Task {task_id} not found in database, cannot save duration!")
                logger.error(f"[SCRAPE_ALL] Available task_ids: {[t.task_id for t in ScrapingTask.query.limit(5).all()]}")
            
            return {
                'status': 'submitted', 
                'tasks_submitted': len(venue_tasks),
                'venues': len(venues), 
                'dates': len(target_dates),
                'message': f'Submitted {len(venue_tasks)} scraping tasks. Results will be saved to database as tasks complete.'
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            
            # Calculate duration even on error
            end_time = time.time()
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60
            
            logger.error(f"[SCRAPE_ALL] Error in scrape_all_venues_task: {e}", exc_info=True)
            logger.error(f"[SCRAPE_ALL] ⏱️  DURATION (failed): {duration_seconds:.2f} seconds ({duration_minutes:.2f} minutes)")
            
            # Always save duration on error (task_id is now guaranteed to exist)
            task = ScrapingTask.query.filter_by(task_id=task_id).first()
            if task:
                task.duration_seconds = duration_seconds
                task.completed_at = datetime.utcnow()
                task.status = 'FAILURE'
                task.error = str(e)
                db.session.commit()
                logger.info(f"[SCRAPE_ALL] Saved duration {duration_seconds:.2f}s to failed task {task_id}")
            raise e


def scrape_restaurants(guests, target_date, website, lawn_club_option=None, lawn_club_time=None, lawn_club_duration=None, spin_time=None, clays_location=None, puttshack_location=None, f1_experience=None):
    """Main scraper function that calls appropriate scraper based on website (legacy - kept for compatibility)"""
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
    # In production, serve React app from frontend/dist
    # For now, return a simple message or redirect
    return jsonify({'message': 'Flask API is running. Use React frontend at http://localhost:3000'})

@app.route('/api/health')
@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        count = AvailabilitySlot.query.count()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'total_slots': count
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# API routes - prefix with /api for React frontend (also support direct routes)
@app.route('/api/test_query')
def test_query():
    """Test endpoint to debug query issues"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Get database info
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_file = os.path.join(basedir, "availability.db")
        db_exists = os.path.exists(db_file)
        db_size = os.path.getsize(db_file) if db_exists else 0
        
        city = request.args.get('city', 'NYC')
        guests = request.args.get('guests', '6')
        
        # Count total
        total_all = AvailabilitySlot.query.count()
        
        # Test direct query
        query1 = AvailabilitySlot.query.filter(
            AvailabilitySlot.city == city,
            AvailabilitySlot.guests == int(guests)
        )
        count1 = query1.count()
        slots = query1.limit(5).all()
        
        # Test without guests filter
        query2 = AvailabilitySlot.query.filter(AvailabilitySlot.city == city)
        count2 = query2.count()
        
        data = []
        for slot in slots:
            try:
                data.append(slot.to_dict())
            except Exception as e:
                data.append({'error': str(e), 'slot_id': slot.id})
        
        return jsonify({
            'database_info': {
                'uri': db_uri,
                'file_path': db_file,
                'file_exists': db_exists,
                'file_size_bytes': db_size
            },
            'city': city,
            'guests': guests,
            'total_slots_in_db': total_all,
            'nyc_total': count2,
            'nyc_with_guests_6': count1,
            'sample_slots': data
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/clear_data', methods=['POST'])
@app.route('/clear_data', methods=['POST'])  # Also support direct route
def api_clear_data():
    """API endpoint for clearing data"""
    return clear_data()


@app.route('/run_scraper', methods=['POST'])
def run_scraper():
    data = request.get_json()
    guests = data.get('guests')
    target_date = data.get('target_date')
    website = data.get('website', 'swingers_nyc')
    lawn_club_option = data.get('lawn_club_option')
    lawn_club_time = data.get('lawn_club_time')
    lawn_club_duration = data.get('lawn_club_duration')
    spin_time = data.get('spin_time')
    clays_location = data.get('clays_location')
    puttshack_location = data.get('puttshack_location')
    f1_experience = data.get("f1_experience")
 
    # Validate and normalize target_date format
    if target_date:
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
            if 'T' in target_date or ' ' in target_date:
                target_date = target_date.split('T')[0].split(' ')[0]
        except ValueError:
            return jsonify({'error': f'Invalid date format: {target_date}. Expected YYYY-MM-DD'}), 400
    
    if not guests:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    required_date_websites = [
        'electric_shuffle_nyc', 'electric_shuffle_london', 'lawn_club_nyc', 'spin_nyc', 
        'five_iron_golf_nyc', 'lucky_strike_nyc', 'easybowl_nyc',
        'fair_game_canary_wharf', 'fair_game_city', 'clays_bar', 'puttshack', 
        'flight_club_darts', 'flight_club_darts_angel', 'flight_club_darts_shoreditch', 
        'flight_club_darts_victoria', 'f1_arcade', 'all_new_york', 'all_london'
    ]
    
    if website in required_date_websites and not target_date:
        if website in ['all_new_york', 'all_london']:
            return jsonify({'error': f'{website.replace("_", " ").title()} requires a specific target date'}), 400
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
    
    # Create task record in database
    import uuid
    task_id = str(uuid.uuid4())
    task = ScrapingTask(
        task_id=task_id,
        website=website,
        guests=guests,
        target_date=datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else None,
        status='PENDING',
        progress='Task queued...'
    )
    db.session.add(task)
    db.session.commit()
    
    # Prepare options
    options = {
        'lawn_club_option': lawn_club_option,
        'lawn_club_time': lawn_club_time,
        'lawn_club_duration': lawn_club_duration,
        'spin_time': spin_time,
        'clays_location': clays_location,
        'puttshack_location': puttshack_location,
        'f1_experience': f1_experience
    }
    
    # Start Celery task
    if website == 'all_new_york':
        result = scrape_all_venues_task.delay('NYC', guests, target_date, task_id, options)
    elif website == 'all_london':
        result = scrape_all_venues_task.delay('London', guests, target_date, task_id, options)
    else:
        result = scrape_venue_task.delay(
            guests=guests,
            target_date=target_date,
            website=website,
            task_id=task_id,
            **options
        )
    
    return jsonify({
        'message': 'Scraping started successfully',
        'task_id': task_id
    })


@app.route('/task_status/<task_id>')
def get_task_status(task_id):
    """Get Celery task status"""
    try:
        # Get task from database
        task = ScrapingTask.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Get Celery task status
        celery_task = AsyncResult(task_id, app=celery_app)
        
        response = {
            'task_id': task_id,
            'status': celery_task.state if celery_task.state else task.status,
            'progress': task.progress,
            'current_venue': task.current_venue,
            'total_slots_found': task.total_slots_found,
            'error': task.error,
            'duration_seconds': task.duration_seconds,
            'completed': celery_task.ready() if celery_task else (task.status in ['SUCCESS', 'FAILURE'])
        }
        
        # Add Celery-specific info
        if celery_task:
            if celery_task.state == 'PENDING':
                response['status'] = 'PENDING'
            elif celery_task.state == 'PROGRESS':
                response['status'] = 'STARTED'
                if celery_task.info:
                    response.update(celery_task.info)
            elif celery_task.state == 'SUCCESS':
                response['status'] = 'SUCCESS'
                if celery_task.result:
                    response['result'] = celery_task.result
            elif celery_task.state == 'FAILURE':
                response['status'] = 'FAILURE'
                response['error'] = str(celery_task.info) if celery_task.info else task.error
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scraping_durations')
@app.route('/scraping_durations')
def get_scraping_durations():
    """Get latest scraping durations for each queue: NYC today, NYC tomorrow, London today, London tomorrow"""
    try:
        # Get latest successful tasks for each queue
        nyc_today_task = ScrapingTask.query.filter_by(
            website='all_nyc_today',
            status='SUCCESS'
        ).order_by(ScrapingTask.completed_at.desc()).first()
        
        nyc_tomorrow_task = ScrapingTask.query.filter_by(
            website='all_nyc_tomorrow',
            status='SUCCESS'
        ).order_by(ScrapingTask.completed_at.desc()).first()
        
        london_today_task = ScrapingTask.query.filter_by(
            website='all_london_today',
            status='SUCCESS'
        ).order_by(ScrapingTask.completed_at.desc()).first()
        
        london_tomorrow_task = ScrapingTask.query.filter_by(
            website='all_london_tomorrow',
            status='SUCCESS'
        ).order_by(ScrapingTask.completed_at.desc()).first()
        
        def format_task_duration(task):
            if task and task.duration_seconds:
                return {
                    'duration_seconds': task.duration_seconds,
                    'duration_minutes': round(task.duration_seconds / 60, 2),
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'total_slots': task.total_slots_found
                }
            return None
        
        durations = {
            'nyc_today': format_task_duration(nyc_today_task),
            'nyc_tomorrow': format_task_duration(nyc_tomorrow_task),
            'london_today': format_task_duration(london_today_task),
            'london_tomorrow': format_task_duration(london_tomorrow_task)
        }
        
        return jsonify(durations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/status')
def get_status():
    """Legacy status endpoint - returns latest task status if available"""
    # Get most recent task
    task = ScrapingTask.query.order_by(ScrapingTask.created_at.desc()).first()
    if task:
        return jsonify({
            'running': task.status == 'STARTED',
            'progress': task.progress or '',
            'completed': task.status == 'SUCCESS',
            'error': task.error,
            'current_date': task.target_date.isoformat() if task.target_date else '',
            'total_slots_found': task.total_slots_found,
            'website': task.website
        })
    return jsonify({
        'running': False,
        'progress': 'Ready to start scraping...',
        'completed': False,
        'error': None,
        'current_date': '',
        'total_slots_found': 0,
        'website': ''
    })


@app.route('/data')
@app.route('/api/data')  # Also support /api/data for React frontend
def get_data():
    """Get scraped data from database"""
    try:
        # Get query parameters
        city = request.args.get('city')
        venue_name = request.args.get('venue_name')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        status_filter = request.args.get('status')
        guests = request.args.get('guests')  # Add guests filter
        search_term = request.args.get('search', '').lower()
        
        # Debug logging - use both print and logger
        import logging
        logger = logging.getLogger(__name__)
        
        # Log database info
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
        debug_db = f"[API DEBUG] Database URI: {db_uri}"
        print(debug_db, flush=True)
        logger.info(debug_db)
        
        # Count total slots before filtering
        total_before = AvailabilitySlot.query.count()
        debug_total = f"[API DEBUG] Total slots in database before filter: {total_before}"
        print(debug_total, flush=True)
        logger.info(debug_total)
        
        debug_msg = f"[API DEBUG] Request params: city={city}, venue_name={venue_name}, date_from={date_from}, date_to={date_to}, guests={guests}, status={status_filter}"
        print(debug_msg, flush=True)
        logger.info(debug_msg)
        
        # Build query
        query = AvailabilitySlot.query
        
        if city:
            # Normalize city values - handle variations
            city_normalized = city.strip()
            # Handle variations: "New York" -> "NYC", "NY" -> "NYC"
            if city_normalized.upper() in ['NEW YORK', 'NY', 'NYC']:
                # For SQLite, match exact "NYC" value (data is stored as "NYC")
                query = query.filter(AvailabilitySlot.city == 'NYC')
                debug_city = f"[API DEBUG] Filtering by city='NYC'"
                print(debug_city, flush=True)
                logger.info(debug_city)
            elif city_normalized.upper() == 'LONDON':
                # Match exact "London" value (data is stored as "London")
                query = query.filter(AvailabilitySlot.city == 'London')
                debug_city = f"[API DEBUG] Filtering by city='London'"
                print(debug_city, flush=True)
                logger.info(debug_city)
            else:
                # Default: exact match (case-sensitive for SQLite)
                query = query.filter(AvailabilitySlot.city == city_normalized)
                debug_city = f"[API DEBUG] Filtering by city='{city_normalized}'"
                print(debug_city, flush=True)
                logger.info(debug_city)
        
        # Debug: Count after city filter
        if city:
            count_after_city = query.count()
            debug_count = f"[API DEBUG] Slots after city filter: {count_after_city}"
            print(debug_count, flush=True)
            logger.info(debug_count)
        if venue_name:
            query = query.filter(AvailabilitySlot.venue_name == venue_name)
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                query = query.filter(AvailabilitySlot.date >= date_from_obj)
            except ValueError as e:
                return jsonify({'error': f'Invalid date_from format: {date_from}. Expected YYYY-MM-DD'}), 400
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                query = query.filter(AvailabilitySlot.date <= date_to_obj)
            except ValueError as e:
                return jsonify({'error': f'Invalid date_to format: {date_to}. Expected YYYY-MM-DD'}), 400
        if guests:
            try:
                guests_int = int(guests)
                query = query.filter(AvailabilitySlot.guests == guests_int)
                debug_guests = f"[API DEBUG] Filtering by guests={guests_int}"
                print(debug_guests, flush=True)
                logger.info(debug_guests)
                # Debug: Count after guests filter
                count_after_guests = query.count()
                debug_count_guests = f"[API DEBUG] Slots after guests filter: {count_after_guests}"
                print(debug_count_guests, flush=True)
                logger.info(debug_count_guests)
            except ValueError:
                pass  # Ignore invalid guest count
        if status_filter:
            query = query.filter(AvailabilitySlot.status.ilike(f'%{status_filter}%'))
        
        # Get all results - when city filter is applied, returns ALL venues in that city
        # Order by date first (newest first), then time, then venue name for consistent date alignment
        slots = query.order_by(
            AvailabilitySlot.date.desc(), 
            AvailabilitySlot.time,
            AvailabilitySlot.venue_name
        ).all()
        
        # Debug logging
        debug_msg = f"[API DEBUG] Query returned {len(slots)} slots"
        print(debug_msg, flush=True)
        logger.info(debug_msg)
        if len(slots) > 0:
            first_slot_msg = f"[API DEBUG] First slot: {slots[0].venue_name}, {slots[0].city}, {slots[0].date}, guests={slots[0].guests}"
            print(first_slot_msg, flush=True)
            logger.info(first_slot_msg)
        
        # Convert to dict and filter by search term if provided
        data = []
        converted_count = 0
        error_count = 0
        for slot in slots:
            try:
                slot_dict = slot.to_dict()
                if not slot_dict.get('booking_url'):
                    slot_dict['booking_url'] = get_booking_url_for_venue(slot_dict.get('venue_name'))
                data.append(slot_dict)
                converted_count += 1
            except Exception as e:
                # Log error but continue processing other slots
                error_msg = f"Error converting slot {slot.id} to dict: {e}"
                print(error_msg, flush=True)
                logger.error(error_msg, exc_info=True)
                error_count += 1
                continue
        
        debug_convert_msg = f"[API DEBUG] Converted {converted_count} slots, {error_count} errors"
        print(debug_convert_msg, flush=True)
        logger.info(debug_convert_msg)
        
        if search_term:
            data = [
                item for item in data
                if search_term in str(item.get('venue_name', '')).lower() or
                   search_term in str(item.get('date', '')).lower() or
                   search_term in str(item.get('time', '')).lower() or
                   search_term in str(item.get('price', '')).lower() or
                   search_term in str(item.get('status', '')).lower()
            ]
        
        return_msg = f"[API DEBUG] Returning {len(data)} items (after search filter: {bool(search_term)})"
        print(return_msg, flush=True)
        logger.info(return_msg)
        return jsonify({
            'data': data,
            'total_count': len(data)
        })
    except Exception as e:
        import traceback
        error_msg = f"[API ERROR] Exception in get_data: {e}"
        print(error_msg, flush=True)
        logger.error(error_msg, exc_info=True)
        traceback.print_exc()
        error_trace = traceback.format_exc()
        print(f"Error in get_data: {e}")
        print(error_trace)
        # Always return JSON, even on error
        try:
            return jsonify({
                'error': str(e),
                'message': f'Error fetching data: {str(e)}',
                'traceback': error_trace.split('\n')[-5:] if error_trace else None  # Last 5 lines only
            }), 500
        except Exception as json_error:
            # Fallback if jsonify fails
            print(f"Error creating JSON response: {json_error}")
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@app.route('/clear_data', methods=['POST'])
def clear_data():
    """Clear scraped data from database"""
    try:
        data = request.get_json() or {}
        city = data.get('city')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        query = AvailabilitySlot.query
        
        if city:
            query = query.filter(AvailabilitySlot.city == city)
        if date_from:
            query = query.filter(AvailabilitySlot.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        if date_to:
            query = query.filter(AvailabilitySlot.date <= datetime.strptime(date_to, "%Y-%m-%d").date())
        
        count = query.delete()
        db.session.commit()
        
        return jsonify({'message': f'Cleared {count} records successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/refresh_data', methods=['POST'])
def refresh_data():
    """Manually trigger data refresh - defaults to today and tomorrow"""
    data = request.get_json() or {}
    city = data.get('city')
    guests = data.get('guests', 6)  # Default to 6 guests
    target_date = data.get('target_date')
    
    from datetime import date, timedelta
    
    # Default to today and tomorrow if no date specified
    if not target_date:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        dates_to_refresh = [today.isoformat(), tomorrow.isoformat()]
    else:
        dates_to_refresh = [target_date] if isinstance(target_date, str) else [target_date]
    
    import uuid
    task_ids = []
    
    for date_str in dates_to_refresh:
        task_id = str(uuid.uuid4())
        task_ids.append(task_id)
        
        task = ScrapingTask(
            task_id=task_id,
            website=f'refresh_{city or "all"}',
            guests=guests,
            target_date=datetime.strptime(date_str, "%Y-%m-%d").date() if isinstance(date_str, str) else date_str,
            status='PENDING',
            progress='Refresh task queued...'
        )
        db.session.add(task)
    
    db.session.commit()
    
    # Start refresh tasks
    for i, date_str in enumerate(dates_to_refresh):
        task_id = task_ids[i]
        if city:
            scrape_all_venues_task.delay(city, guests, date_str, task_id)
        else:
            # Refresh both cities
            scrape_all_venues_task.delay('NYC', guests, date_str, task_id)
            scrape_all_venues_task.delay('London', guests, date_str, task_id)
    
    return jsonify({
        'message': f'Refresh started successfully for {len(dates_to_refresh)} date(s)',
        'task_ids': task_ids
    })


if __name__ == '__main__':
    # Bind to 0.0.0.0 to allow external access (for VPS)
    # Set host='127.0.0.1' for localhost only (more secure for development)
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    # Disable debug mode in production to reduce log volume
    # Set FLASK_DEBUG=1 in .env for development only
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(debug=debug_mode, host=host, port=8010)