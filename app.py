from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import quote_plus, urlencode
from celery import group, chord
from celery.result import AsyncResult
from sqlalchemy import inspect, text, or_, create_engine
from sqlalchemy.engine.url import make_url
import time
import logging
import sys
import uuid

from models import db, AvailabilitySlot, ScrapingTask

# Import celery_app after app is created to avoid circular import
try:
    from celery_app import celery_app
except ImportError:
    celery_app = None

# Set instance_path to None to prevent Flask from using instance folder for database
app = Flask(__name__, instance_path=None, instance_relative_config=False)

# Enable CORS for React frontend
CORS(app, resources={r"/*": {"origins": "*"}})

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
# Use absolute path for SQLite to avoid working directory issues
# IMPORTANT: SQLite URLs need 4 slashes for absolute paths: sqlite:////absolute/path
db_file_path = os.path.join(basedir, "availability.db")
# Use 4 slashes to ensure absolute path (sqlite:////path/to/file.db)
# This prevents Flask from using the instance folder
database_url = os.getenv('DATABASE_URL', f'sqlite:////{db_file_path}')

# Debug: Log the database configuration
logger_init = logging.getLogger(__name__)
logger_init.info(f"[INIT] Database file path: {db_file_path}")
logger_init.info(f"[INIT] Database URL: {database_url}")
logger_init.info(f"[INIT] Database file exists: {os.path.exists(db_file_path)}")

# Configure SQLite for better concurrency
# CRITICAL: Set database URI BEFORE initializing db to prevent Flask instance folder usage
# Force absolute path with 4 slashes to prevent Flask instance folder usage
absolute_db_url = f'sqlite:////{db_file_path}'
app.config['SQLALCHEMY_DATABASE_URI'] = absolute_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if database_url.startswith('sqlite'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {
            'timeout': 30,
            'check_same_thread': False
        }
    }
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }

# Initialize database - MUST be after setting SQLALCHEMY_DATABASE_URI
# The absolute_db_url is already set in app.config, so db.init_app should use it
db.init_app(app)

# Verify the database URI was set correctly
with app.app_context():
    actual_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')
    logger_init.info(f"[INIT] SQLAlchemy URI in config: {actual_uri}")
    # Check what engine URL SQLAlchemy is actually using
    try:
        engine_url = str(db.engine.url)
        logger_init.info(f"[INIT] SQLAlchemy engine URL: {engine_url}")
        # If it's still using instance folder, log a warning
        if 'instance' in engine_url:
            logger_init.error(f"[INIT] ERROR: Engine is still using instance folder! Expected: {absolute_db_url}, Got: {engine_url}")
    except Exception as e:
        logger_init.warning(f"[INIT] Could not get engine URL: {e}")

# Enable WAL mode for SQLite after initialization
if database_url.startswith('sqlite'):
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                # Check current journal mode
                result = conn.execute(text("PRAGMA journal_mode"))
                current_mode = result.scalar()
                logger = logging.getLogger(__name__)
                logger.info(f"Current SQLite journal mode: {current_mode}")
                
                # Enable WAL mode
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.execute(text("PRAGMA busy_timeout=30000"))
                
                # Checkpoint WAL to ensure data is visible
                conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                conn.commit()
                
                # Verify WAL mode is active
                result2 = conn.execute(text("PRAGMA journal_mode"))
                new_mode = result2.scalar()
                logger.info(f"SQLite journal mode after setup: {new_mode}")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not enable WAL mode for SQLite: {e}")

# Create tables and ensure latest schema
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('availability_slots')]
    if 'booking_url' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE availability_slots ADD COLUMN booking_url VARCHAR(500)"))

# Venue lists
NYC_VENUES = [
    'swingers_nyc',
    'electric_shuffle_nyc',
    'lawn_club_nyc_indoor_gaming',
    'lawn_club_nyc_curling_lawns',
    'lawn_club_nyc_croquet_lawns',
    'spin_nyc',
    'spin_nyc_midtown',
    'five_iron_golf_nyc_fidi',
    'five_iron_golf_nyc_flatiron',
    'five_iron_golf_nyc_grand_central',
    'five_iron_golf_nyc_herald_square',
    'five_iron_golf_nyc_long_island_city',
    'five_iron_golf_nyc_upper_east_side',
    'five_iron_golf_nyc_rockefeller_center',
    'lucky_strike_nyc',
    'lucky_strike_nyc_times_square',
    'easybowl_nyc',
    'tsquaredsocial_nyc',
    'daysmart_chelsea',
    'puttery_nyc',
    'kick_axe_brooklyn'
]

LONDON_VENUES = [
    'swingers_london',
    'electric_shuffle_london',
    'fair_game_canary_wharf',
    'fair_game_city',
    'clays_bar',
    'puttshack',
    'flight_club_darts',  # Single entry - scrapes all 4 locations in one task
    'f1_arcade',
    'topgolf_chigwell',
    'hijingo',
    'pingpong',
    'allstarlanes_stratford',
    'allstarlanes_holborn',
    'allstarlanes_white_city',
    'allstarlanes_brick_lane'
]

VENUE_BOOKING_URLS = {
    'Swingers (NYC)': 'https://www.swingers.club/us/locations/nyc/book-now',
    'Swingers (London)': 'https://www.swingers.club/uk/book-now',
    'Electric Shuffle (NYC)': 'https://www.sevenrooms.com/explore/electricshufflenyc/reservations/create/search',
    'Electric Shuffle (London)': 'https://electricshuffle.com/uk/london/book',
    'Lawn Club NYC': 'https://www.sevenrooms.com/landing/lawnclubnyc',
    'Lawn Club (Indoor Gaming)': 'https://www.sevenrooms.com/landing/lawnclubnyc',
    'Lawn Club (Curling Lawns)': 'https://www.sevenrooms.com/landing/lawnclubnyc',
    'Lawn Club (Croquet Lawns)': 'https://www.sevenrooms.com/landing/lawnclubnyc',
    'SPIN (NYC)': 'https://wearespin.com/location/new-york-flatiron/table-reservations/',
    'SPIN (NYC - Flatiron)': 'https://wearespin.com/location/new-york-flatiron/table-reservations/',
    'SPIN (NYC - Midtown)': 'https://wearespin.com/location/new-york-midtown/table-reservations/',
    'Five Iron Golf (NYC)': 'https://booking.fiveirongolf.com/session-length',
    'Five Iron Golf (NYC - FiDi)': 'https://booking.fiveirongolf.com/session-length',
    'Five Iron Golf (NYC - Flatiron)': 'https://booking.fiveirongolf.com/session-length',
    'Five Iron Golf (NYC - Grand Central)': 'https://booking.fiveirongolf.com/session-length',
    'Five Iron Golf (NYC - Herald Square)': 'https://booking.fiveirongolf.com/session-length',
    'Five Iron Golf (NYC - Long Island City)': 'https://booking.fiveirongolf.com/session-length',
    'Five Iron Golf (NYC - Upper East Side)': 'https://booking.fiveirongolf.com/session-length',
    'Five Iron Golf (NYC - Rockefeller Center)': 'https://booking.fiveirongolf.com/session-length',
    'Lucky Strike (Chelsea Piers)': 'https://www.luckystrikeent.com/location/lucky-strike-chelsea-piers/booking/lane-reservation',
    'Lucky Strike (Times Square)': 'https://www.luckystrikeent.com/location/lucky-strike-times-square/booking/lane-reservation',
    'Easybowl (NYC)': 'https://www.easybowl.com/bc/LET/booking',
    'T-Squared Social': 'https://www.opentable.com/booking/restref/availability?lang=en-US&restRef=1331374&otSource=Restaurant%20website',
    'Chelsea Piers Golf': 'https://apps.daysmartrecreation.com/dash/chelsea/program-finder',
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
    'F1 Arcade': 'https://f1arcade.com/uk/booking/venue/london',
    'Topgolf Chigwell': 'https://www.sevenrooms.com/explore/topgolfchigwell/reservations/create/search',
    'Bounce': 'https://bookings.designmynight.com/book?widget_version=2&venue_id=512b203fd5d190d2978ca644&venue_group=5536821278727915249864d6&type=5955253c91c098669b3202d3&duration=55&marketing_preferences=&tags=%7B%7D&source=partner&return_url=https%3A%2F%2Fwww.bouncepingpong.com%2Fapi%2Fbooking-confirmed%2F&return_method=post&gtm_account=Farringdon_booknow&locale=en-GB',
    'Puttery (NYC)': 'https://www.exploretock.com/puttery-new-york/experience/556314/play-1-course-reservation-weekday',
    'Kick Axe (Brooklyn)': 'https://www.exploretock.com/kick-axe-throwing-brooklyn-2025/experience/573671/axe-throwing-75-mins'
}


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


def adjust_picker(page, value_selector, increment_selector, decrement_selector, valid_values, target_value, normalize_fn=None):
    """Use picker arrows to land on requested value (Playwright version)."""
    from bs4 import BeautifulSoup
    
    normalizer = normalize_fn or (lambda v: v)
    normalized_target = normalizer(target_value)

    normalized_values = [normalizer(val) for val in valid_values]
    if normalized_target not in normalized_values:
        raise ValueError(f"Unsupported value '{target_value}' for picker")
    
    max_attempts = len(valid_values) * 2
    for _ in range(max_attempts):
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")
        button = soup.select_one(value_selector)
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
            page.click(click_selector)
        except Exception:
            pass
        
        page.wait_for_timeout(250)
    
    return False


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
    if venue_name in VENUE_BOOKING_URLS:
        return VENUE_BOOKING_URLS[venue_name]
    normalized = venue_name.split('(')[0].strip()
    for known_name, url in VENUE_BOOKING_URLS.items():
        if normalized and normalized.lower() in known_name.lower():
            return url
    return build_booking_search_url(venue_name)


def retry_db_operation(func, max_retries=5, delay=0.1):
    """Retry a database operation if it fails due to database lock"""
    from sqlalchemy.exc import OperationalError
    
    for attempt in range(max_retries):
        try:
            return func()
        except OperationalError as e:
            error_str = str(e).lower()
            if 'locked' in error_str or 'database is locked' in error_str:
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            else:
                raise
        except Exception as e:
            raise
    return None


def cleanup_old_slots():
    """Remove availability slots with dates before today"""
    logger = logging.getLogger(__name__)
    
    def _cleanup_operation():
        from datetime import date
        today = date.today()
        
        # Count slots to be deleted
        old_slots_count = AvailabilitySlot.query.filter(AvailabilitySlot.date < today).count()
        
        if old_slots_count > 0:
            # Delete old slots using bulk delete
            deleted_count = AvailabilitySlot.query.filter(AvailabilitySlot.date < today).delete(synchronize_session=False)
            db.session.commit()
            logger.info(f"[CLEANUP] Deleted {deleted_count} old availability slots (dates before {today})")
            return deleted_count
        else:
            logger.info(f"[CLEANUP] No old slots to delete (all slots are from {today} or later)")
            return 0
    
    try:
        return retry_db_operation(_cleanup_operation)
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error cleaning up old slots: {e}")
        return 0


def save_slot_to_db(venue_name, date_str, time, price, status, guests, city, venue_specific_data=None, booking_url=None):
    """Save or update availability slot in database with retry logic for lock errors"""
    def _save_operation():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date() if isinstance(date_str, str) else date_str
        effective_booking_url = get_booking_url_for_venue(venue_name, booking_url)
        
        existing = AvailabilitySlot.query.filter_by(
            venue_name=venue_name,
            date=date_obj,
            time=time,
            guests=guests
        ).first()
        
        if existing:
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
    
    try:
        return retry_db_operation(_save_operation)
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving slot to database after retries: {e}")
        return None


def update_task_status(task_id, status=None, progress=None, current_venue=None, total_slots=None, error=None):
    """Update scraping task status in database with retry logic for lock errors"""
    def _update_operation():
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
            return True
        return False
    
    try:
        return retry_db_operation(_update_operation)
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating task status after retries: {e}")
        return False


def run_scraper_and_save_to_db(scraper_func, venue_name, city, guests, *args, task_id=None, **kwargs):
    """Run scraper function and save results to database"""
    logger = logging.getLogger(__name__)
    
    print(f"[SCRAPER] Starting scraper for {venue_name} (city: {city}, guests: {guests})", flush=True)
    logger.info(f"[SCRAPER] Starting scraper for {venue_name} (city: {city}, guests: {guests})")
    sys.stdout.flush()
    
    # Run the scraper function
    try:
        logger.info(f"[SCRAPER] Calling scraper function for {venue_name}...")
        results = scraper_func(*args, **kwargs)
        logger.info(f"[SCRAPER] Scraper function completed for {venue_name}")
    except Exception as e:
        logger.error(f"[SCRAPER] Error in scraper function for {venue_name}: {e}", exc_info=True)
        if task_id:
            update_task_status(task_id, status='FAILURE', error=str(e))
        raise e
    
    # Save all results to database
    slots_saved = 0
    if not results:
        results = []
    
    logger.info(f"[SCRAPER] {venue_name}: Found {len(results)} items, saving to database...")
    
    for item in results:
        item_venue_name = item.get('website', venue_name)
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
    
    logger.info(f"[SCRAPER] {venue_name}: Successfully saved {slots_saved} slots to database")
    
    return slots_saved


# Import scrapers
from scrapers import swingers, electric_shuffle, lawn_club, spin, five_iron_golf, lucky_strike, easybowl
from scrapers import fair_game, clays_bar, puttshack, flight_club_darts, f1_arcade, topgolfchigwell, tsquaredsocial, daysmart, hijingo, pingpong, puttery, kick_axe, allstarlanes_bowling

# Flask Routes
@app.route('/')
def index():
    return jsonify({'message': 'Flask API is running. Use React frontend at http://localhost:3000'})

@app.route('/api/health')
@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
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

@app.route('/api/cleanup_old_slots', methods=['POST'])
def cleanup_old_slots_endpoint():
    """Manual endpoint to clean up old availability slots (dates before today)"""
    try:
        deleted_count = cleanup_old_slots()
        return jsonify({
            'status': 'success',
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} old availability slots'
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in cleanup endpoint: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/test_query')
def test_query():
    """Test endpoint to debug query issues"""
    try:
        logger = logging.getLogger(__name__)
        
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_file = os.path.join(basedir, "availability.db")
        db_exists = os.path.exists(db_file)
        db_size = os.path.getsize(db_file) if db_exists else 0
        
        city = request.args.get('city', 'NYC')
        guests = request.args.get('guests', '6')
        
        total_all = AvailabilitySlot.query.count()
        
        # Get all unique cities
        all_cities = db.session.query(AvailabilitySlot.city.distinct()).all()
        unique_cities = [c[0] for c in all_cities]
        
        # Get all unique venue names
        all_venues = db.session.query(AvailabilitySlot.venue_name.distinct()).limit(20).all()
        unique_venues = [v[0] for v in all_venues]
        
        # Get all unique guest counts
        all_guests = db.session.query(AvailabilitySlot.guests.distinct()).all()
        unique_guests = sorted([g[0] for g in all_guests])
        
        query1 = AvailabilitySlot.query.filter(
            AvailabilitySlot.city == city,
            AvailabilitySlot.guests == int(guests)
        )
        count1 = query1.count()
        slots = query1.limit(5).all()
        
        query2 = AvailabilitySlot.query.filter(AvailabilitySlot.city == city)
        count2 = query2.count()
        
        # Query without city filter
        query3 = AvailabilitySlot.query
        count3 = query3.count()
        
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
            'total_with_city_filter': count2,
            'total_with_city_and_guests_filter': count1,
            'total_no_filters': count3,
            'unique_cities_in_db': unique_cities,
            'unique_venues_in_db': unique_venues,
            'unique_guests_in_db': unique_guests,
            'sample_slots': data
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/clear_data', methods=['POST'])
@app.route('/clear_data', methods=['POST'])
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
        'electric_shuffle_nyc', 'electric_shuffle_london', 'lawn_club_nyc_indoor_gaming', 
        'lawn_club_nyc_curling_lawns', 'lawn_club_nyc_croquet_lawns', 'spin_nyc', 'spin_nyc_midtown', 
        'five_iron_golf_nyc_fidi', 'five_iron_golf_nyc_flatiron', 'five_iron_golf_nyc_grand_central',
        'five_iron_golf_nyc_herald_square', 'five_iron_golf_nyc_long_island_city',
        'five_iron_golf_nyc_upper_east_side', 'five_iron_golf_nyc_rockefeller_center',
        'lucky_strike_nyc', 'lucky_strike_nyc_times_square', 'easybowl_nyc',
        'fair_game_canary_wharf', 'fair_game_city', 'clays_bar', 'puttshack', 
        'flight_club_darts', 'f1_arcade', 'hijingo', 'pingpong', 'puttery_nyc',
        'kick_axe_brooklyn',
        'allstarlanes_stratford', 'allstarlanes_holborn', 'allstarlanes_white_city', 'allstarlanes_brick_lane',
        'all_new_york', 'all_london'
    ]
    
    if website in required_date_websites and not target_date:
        if website in ['all_new_york', 'all_london']:
            return jsonify({'error': f'{website.replace("_", " ").title()} requires a specific target date'}), 400
        website_names = {
            'electric_shuffle_nyc': 'Electric Shuffle NYC',
            'electric_shuffle_london': 'Electric Shuffle London',
            'lawn_club_nyc_indoor_gaming': 'Lawn Club (Indoor Gaming)',
            'lawn_club_nyc_curling_lawns': 'Lawn Club (Curling Lawns)',
            'lawn_club_nyc_croquet_lawns': 'Lawn Club (Croquet Lawns)',
            'spin_nyc': 'SPIN (NYC - Flatiron)',
            'spin_nyc_midtown': 'SPIN (NYC - Midtown)',
            'five_iron_golf_nyc_fidi': 'Five Iron Golf (NYC - FiDi)',
            'five_iron_golf_nyc_flatiron': 'Five Iron Golf (NYC - Flatiron)',
            'five_iron_golf_nyc_grand_central': 'Five Iron Golf (NYC - Grand Central)',
            'five_iron_golf_nyc_herald_square': 'Five Iron Golf (NYC - Herald Square)',
            'five_iron_golf_nyc_long_island_city': 'Five Iron Golf (NYC - Long Island City)',
            'five_iron_golf_nyc_upper_east_side': 'Five Iron Golf (NYC - Upper East Side)',
            'five_iron_golf_nyc_rockefeller_center': 'Five Iron Golf (NYC - Rockefeller Center)',
            'lucky_strike_nyc': 'Lucky Strike (Chelsea Piers)',
            'lucky_strike_nyc_times_square': 'Lucky Strike (Times Square)',
            'easybowl_nyc': 'Easybowl NYC',
            'fair_game_canary_wharf': 'Fair Game (Canary Wharf)',
            'fair_game_city': 'Fair Game (City)',
            'clays_bar': 'Clays Bar',
            'puttshack': 'Puttshack',
            'flight_club_darts': 'Flight Club Darts (all locations)',
            'f1_arcade': 'F1 Arcade',
            'puttery_nyc': 'Puttery (NYC)',
            'kick_axe_brooklyn': 'Kick Axe (Brooklyn)'
        }
        
        # Handle dynamic venue names for Five Iron Golf, Lawn Club, SPIN, and All Star Lanes
        if website.startswith('five_iron_golf_nyc_'):
            from scrapers.five_iron_golf import FIVE_IRON_VENUE_NAMES
            location = website.replace('five_iron_golf_nyc_', '')
            venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf NYC')
        elif website.startswith('lawn_club_nyc_'):
            from scrapers.lawn_club import LAWN_CLUB_VENUE_NAMES
            option = website.replace('lawn_club_nyc_', '')
            venue_name = LAWN_CLUB_VENUE_NAMES.get(option, 'Lawn Club (Indoor Gaming)')
        elif website.startswith('spin_nyc_'):
            from scrapers.spin import SPIN_VENUE_NAMES
            location = website.replace('spin_nyc_', '')
            venue_name = SPIN_VENUE_NAMES.get(location, 'SPIN (NYC - Flatiron)')
        elif website.startswith('allstarlanes_'):
            from scrapers.allstarlanes_bowling import ALLSTARLANES_VENUE_NAMES
            location = website.replace('allstarlanes_', '')
            venue_name = ALLSTARLANES_VENUE_NAMES.get(location, 'All Star Lanes')
        else:
            venue_name = website_names.get(website, website.replace('_', ' ').title())
        
        return jsonify({'error': f'{venue_name} requires a specific target date'}), 400
    
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
    
    options = {
        'lawn_club_option': lawn_club_option,
        'lawn_club_time': lawn_club_time,
        'lawn_club_duration': lawn_club_duration,
        'spin_time': spin_time,
        'clays_location': clays_location,
        'puttshack_location': puttshack_location,
        'f1_experience': f1_experience
    }
    
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
        task = ScrapingTask.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
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
    """Get latest scraping durations for each queue"""
    try:
        logger = logging.getLogger(__name__)
        
        nyc_today_task = None
        nyc_tomorrow_task = None
        london_today_task = None
        london_tomorrow_task = None
        last_task = None
        
        try:
            nyc_today_task = ScrapingTask.query.filter_by(
                website='all_nyc_today',
                status='SUCCESS'
            ).order_by(ScrapingTask.completed_at.desc()).first()
        except Exception as e:
            logger.warning(f"[API] Error fetching nyc_today_task: {e}")
        
        try:
            nyc_tomorrow_task = ScrapingTask.query.filter_by(
                website='all_nyc_tomorrow',
                status='SUCCESS'
            ).order_by(ScrapingTask.completed_at.desc()).first()
        except Exception as e:
            logger.warning(f"[API] Error fetching nyc_tomorrow_task: {e}")
        
        try:
            london_today_task = ScrapingTask.query.filter_by(
                website='all_london_today',
                status='SUCCESS'
            ).order_by(ScrapingTask.completed_at.desc()).first()
        except Exception as e:
            logger.warning(f"[API] Error fetching london_today_task: {e}")
        
        try:
            london_tomorrow_task = ScrapingTask.query.filter_by(
                website='all_london_tomorrow',
                status='SUCCESS'
            ).order_by(ScrapingTask.completed_at.desc()).first()
        except Exception as e:
            logger.warning(f"[API] Error fetching london_tomorrow_task: {e}")
        
        try:
            last_task = ScrapingTask.query.filter(
                ScrapingTask.status == 'SUCCESS',
                ScrapingTask.duration_seconds.isnot(None),
                ScrapingTask.duration_seconds > 0
            ).order_by(ScrapingTask.completed_at.desc()).first()
        except Exception as e:
            logger.warning(f"[API] Error fetching last_task: {e}")
        
        def format_task_duration(task):
            if task and task.duration_seconds:
                return {
                    'duration_seconds': task.duration_seconds,
                    'duration_minutes': round(task.duration_seconds / 60, 2),
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'total_slots': task.total_slots_found,
                    'website': task.website
                }
            return None
        
        durations = {
            'nyc_today': format_task_duration(nyc_today_task),
            'nyc_tomorrow': format_task_duration(nyc_tomorrow_task),
            'london_today': format_task_duration(london_today_task),
            'london_tomorrow': format_task_duration(london_tomorrow_task),
            'last_duration': format_task_duration(last_task)
        }
        
        return jsonify(durations)
    except Exception as e:
        import traceback
        logger = logging.getLogger(__name__)
        error_msg = f"[API ERROR] Exception in get_scraping_durations: {e}"
        logger.error(error_msg, exc_info=True)
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'message': f'Error fetching scraping durations: {str(e)}'
        }), 500

@app.route('/status')
def get_status():
    """Legacy status endpoint"""
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
@app.route('/api/data')
def get_data():
    """Get scraped data from database"""
    try:
        city = request.args.get('city')
        venue_name = request.args.get('venue_name')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        status_filter = request.args.get('status')
        guests = request.args.get('guests')
        search_term = request.args.get('search', '').lower()
        
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        
        # No default limit - return all results if limit is not specified
        # Maximum limit cap to prevent excessive memory usage
        if limit is not None and limit > 50000:
            limit = 50000
        
        logger = logging.getLogger(__name__)
        
        debug_msg = f"[API DEBUG] Request params: city={city}, venue_name={venue_name}, date_from={date_from}, date_to={date_to}, guests={guests}, status={status_filter}, limit={limit if limit is not None else 'unlimited'}, offset={offset}"
        print(debug_msg, flush=True)
        logger.info(debug_msg)
        
        # Force checkpoint WAL before querying to ensure we see latest data
        # This is important when Celery workers write data while Flask reads
        try:
            with db.engine.connect() as conn:
                conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not checkpoint WAL: {e}")
        
        query = AvailabilitySlot.query
        
        if city:
            city_normalized = city.strip()
            if city_normalized.upper() in ['NEW YORK', 'NY', 'NYC']:
                query = query.filter(AvailabilitySlot.city == 'NYC')
            elif city_normalized.upper() == 'LONDON':
                query = query.filter(AvailabilitySlot.city == 'London')
            else:
                query = query.filter(AvailabilitySlot.city == city_normalized)
        
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
            except ValueError:
                pass
        if status_filter:
            query = query.filter(AvailabilitySlot.status.ilike(f'%{status_filter}%'))
        
        try:
            total_count = query.count()
            debug_count_msg = f"[API DEBUG] Total matching slots before limit/offset: {total_count}"
            print(debug_count_msg, flush=True)
            logger.info(debug_count_msg)
        except Exception as count_error:
            logger.warning(f"[API DEBUG] Could not get total count: {count_error}")
            total_count = None
        
        # Debug: Check what's actually in the database
        if total_count == 0:
            # Show which database file is being used
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
            basedir_debug = os.path.abspath(os.path.dirname(__file__))
            db_file_debug = os.path.join(basedir_debug, "availability.db")
            db_exists_debug = os.path.exists(db_file_debug)
            db_size_debug = os.path.getsize(db_file_debug) if db_exists_debug else 0
            
            # Check for WAL and SHM files
            wal_file = db_file_debug + "-wal"
            shm_file = db_file_debug + "-shm"
            wal_exists = os.path.exists(wal_file)
            shm_exists = os.path.exists(shm_file)
            wal_size = os.path.getsize(wal_file) if wal_exists else 0
            shm_size = os.path.getsize(shm_file) if shm_exists else 0
            
            debug_db_path_msg = f"[API DEBUG] Database URI: {db_uri}, File path: {db_file_debug}, Exists: {db_exists_debug}, Size: {db_size_debug} bytes, WAL: {wal_exists} ({wal_size} bytes), SHM: {shm_exists} ({shm_size} bytes)"
            print(debug_db_path_msg, flush=True)
            logger.info(debug_db_path_msg)
            
            # Try direct SQL query to check if data exists
            try:
                # Get the actual database file path from the engine
                engine_url = str(db.engine.url)
                debug_engine_msg = f"[API DEBUG] SQLAlchemy engine URL: {engine_url}"
                print(debug_engine_msg, flush=True)
                logger.info(debug_engine_msg)
                
                with db.engine.connect() as conn:
                    # Force a full WAL checkpoint to merge all WAL data into main database
                    try:
                        conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                        conn.commit()
                        logger.info("[API DEBUG] WAL checkpoint (TRUNCATE) completed")
                    except Exception as checkpoint_error:
                        logger.warning(f"[API DEBUG] WAL checkpoint failed: {checkpoint_error}")
                    
                    result = conn.execute(text("SELECT COUNT(*) FROM availability_slots"))
                    direct_count = result.scalar()
                    debug_direct_msg = f"[API DEBUG] Direct SQL query count: {direct_count}"
                    print(debug_direct_msg, flush=True)
                    logger.info(debug_direct_msg)
                    
                    # Check table structure
                    result2 = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='availability_slots'"))
                    table_exists = result2.fetchone() is not None
                    debug_table_msg = f"[API DEBUG] Table 'availability_slots' exists: {table_exists}"
                    print(debug_table_msg, flush=True)
                    logger.info(debug_table_msg)
                    
                    # Check journal mode
                    result3 = conn.execute(text("PRAGMA journal_mode"))
                    journal_mode = result3.scalar()
                    debug_journal_msg = f"[API DEBUG] Journal mode: {journal_mode}"
                    print(debug_journal_msg, flush=True)
                    logger.info(debug_journal_msg)
                    
                    if direct_count > 0:
                        # Get sample data
                        result4 = conn.execute(text("SELECT city, guests, COUNT(*) FROM availability_slots GROUP BY city, guests LIMIT 5"))
                        samples = result4.fetchall()
                        debug_samples_msg = f"[API DEBUG] Sample data (city, guests, count): {samples}"
                        print(debug_samples_msg, flush=True)
                        logger.info(debug_samples_msg)
                    else:
                        # If direct SQL returns 0 but file has data, there's a connection issue
                        debug_warning_msg = f"[API DEBUG] WARNING: Direct SQL returns 0 but file size is {db_size_debug} bytes - possible database connection mismatch or WAL not checkpointed!"
                        print(debug_warning_msg, flush=True)
                        logger.warning(debug_warning_msg)
            except Exception as sql_error:
                debug_sql_error_msg = f"[API DEBUG] Error executing direct SQL: {sql_error}"
                print(debug_sql_error_msg, flush=True)
                logger.error(debug_sql_error_msg, exc_info=True)
            
            all_slots_count = AvailabilitySlot.query.count()
            debug_all_msg = f"[API DEBUG] Total slots in database (no filters): {all_slots_count}"
            print(debug_all_msg, flush=True)
            logger.info(debug_all_msg)
            
            # Show sample cities and venue names
            sample_slots = AvailabilitySlot.query.limit(10).all()
            if sample_slots:
                sample_cities = set(s.city for s in sample_slots)
                sample_venues = set(s.venue_name for s in sample_slots)
                sample_guests = set(s.guests for s in sample_slots)
                debug_sample_msg = f"[API DEBUG] Sample cities in DB: {sample_cities}, Sample venues: {list(sample_venues)[:5]}, Sample guests: {sorted(sample_guests)}"
                print(debug_sample_msg, flush=True)
                logger.info(debug_sample_msg)
            
            # Show what the query filter would match
            if city:
                city_filtered = AvailabilitySlot.query.filter(AvailabilitySlot.city == ('NYC' if city.upper() in ['NEW YORK', 'NY', 'NYC'] else 'London' if city.upper() == 'LONDON' else city)).count()
                debug_city_filter_msg = f"[API DEBUG] Slots matching city filter '{city}': {city_filtered}"
                print(debug_city_filter_msg, flush=True)
                logger.info(debug_city_filter_msg)
            
            if guests:
                try:
                    guests_int = int(guests)
                    guests_filtered = AvailabilitySlot.query.filter(AvailabilitySlot.guests == guests_int).count()
                    debug_guests_filter_msg = f"[API DEBUG] Slots matching guests filter '{guests}': {guests_filtered}"
                    print(debug_guests_filter_msg, flush=True)
                    logger.info(debug_guests_filter_msg)
                except ValueError:
                    pass
        
        slots_query = query.order_by(
            AvailabilitySlot.date.desc(), 
            AvailabilitySlot.time,
            AvailabilitySlot.venue_name
        )
        
        if offset > 0:
            slots_query = slots_query.offset(offset)
        if limit is not None:
            slots_query = slots_query.limit(limit)
        
        slots = slots_query.all()
        
        debug_msg = f"[API DEBUG] Query returned {len(slots)} slots (limit={limit if limit is not None else 'unlimited'}, offset={offset})"
        print(debug_msg, flush=True)
        logger.info(debug_msg)
        
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
                error_msg = f"Error converting slot {slot.id} to dict: {e}"
                print(error_msg, flush=True)
                logger.error(error_msg, exc_info=True)
                error_count += 1
                continue
        
        if search_term:
            data = [
                item for item in data
                if search_term in str(item.get('venue_name', '')).lower() or
                   search_term in str(item.get('date', '')).lower() or
                   search_term in str(item.get('time', '')).lower() or
                   search_term in str(item.get('price', '')).lower() or
                   search_term in str(item.get('status', '')).lower()
            ]
        
        response_data = {
            'data': data,
            'total_count': len(data),
            'limit': limit if limit is not None else 'unlimited',
            'offset': offset
        }
        
        if total_count is not None:
            response_data['total_available'] = total_count
        
        # Debug: Log response summary
        debug_response_msg = f"[API DEBUG] Returning {len(data)} items in response (total_available: {total_count})"
        print(debug_response_msg, flush=True)
        logger.info(debug_response_msg)
        
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_msg = f"[API ERROR] Exception in get_data: {e}"
        print(error_msg, flush=True)
        logger = logging.getLogger(__name__)
        logger.error(error_msg, exc_info=True)
        traceback.print_exc()
        error_trace = traceback.format_exc()
        try:
            return jsonify({
                'error': str(e),
                'message': f'Error fetching data: {str(e)}',
                'traceback': error_trace.split('\n')[-5:] if error_trace else None
            }), 500
        except Exception as json_error:
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
    """Manually trigger data refresh"""
    data = request.get_json() or {}
    city = data.get('city')
    guests = data.get('guests', 6)
    target_date = data.get('target_date')
    
    from datetime import date
    
    if not target_date:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        dates_to_refresh = [today.isoformat(), tomorrow.isoformat()]
    else:
        dates_to_refresh = [target_date] if isinstance(target_date, str) else [target_date]
    
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
            progress='Task queued...'
        )
        db.session.add(task)
    
    db.session.commit()
    
    options = {}
    for task_id in task_ids:
        if city == 'NYC' or not city:
            scrape_all_venues_task.delay('NYC', guests, dates_to_refresh, task_id, options)
        if city == 'London' or not city:
            scrape_all_venues_task.delay('London', guests, dates_to_refresh, task_id, options)
    
    return jsonify({
        'message': f'Refresh tasks started for {len(dates_to_refresh)} date(s)',
        'task_ids': task_ids
    })


# Celery Tasks
@celery_app.task(bind=True, name='app.scrape_swingers_task')
def scrape_swingers_task(self, guests, target_date, task_id=None):
    """Swingers NYC scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Swingers NYC...', current_venue='Swingers (NYC)')
            
            slots_saved = run_scraper_and_save_to_db(
                swingers.scrape_swingers,
                'Swingers (NYC)',
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


@celery_app.task(bind=True, name='app.scrape_swingers_uk_task')
def scrape_swingers_uk_task(self, guests, target_date, task_id=None):
    """Swingers UK scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Swingers UK...', current_venue='Swingers (London)')
            
            slots_saved = run_scraper_and_save_to_db(
                swingers.scrape_swingers_uk,
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
                electric_shuffle.scrape_electric_shuffle,
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
                electric_shuffle.scrape_electric_shuffle_london,
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
            # Map option to venue name
            from scrapers.lawn_club import LAWN_CLUB_VENUE_NAMES
            venue_name = LAWN_CLUB_VENUE_NAMES.get(option, f'Lawn Club ({option})')
            
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                lawn_club.scrape_lawn_club,
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
def scrape_spin_task(self, guests, target_date, task_id=None, selected_time=None, location='flatiron'):
    """SPIN scraper as Celery task"""
    with app.app_context():
        try:
            from scrapers.spin import SPIN_VENUE_NAMES
            venue_name = SPIN_VENUE_NAMES.get(location, 'SPIN (NYC - Flatiron)')
            
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                spin.scrape_spin,
                venue_name,
                'NYC',
                guests,
                guests,
                target_date,
                selected_time,
                location,
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
def scrape_five_iron_golf_task(self, guests, target_date, task_id=None, location='fidi'):
    """Five Iron Golf scraper as Celery task"""
    with app.app_context():
        try:
            # Map location to venue name
            from scrapers.five_iron_golf import FIVE_IRON_VENUE_NAMES
            venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf (NYC - FiDi)')
            
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                five_iron_golf.scrape_five_iron_golf,
                venue_name,
                'NYC',
                guests,
                guests,
                target_date,
                location,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_allstarlanes_task')
def scrape_allstarlanes_task(self, guests, target_date, task_id=None, location='stratford'):
    """All Star Lanes scraper as Celery task"""
    with app.app_context():
        try:
            # Map location to venue name
            from scrapers.allstarlanes_bowling import ALLSTARLANES_VENUE_NAMES
            venue_name = ALLSTARLANES_VENUE_NAMES.get(location, 'All Star Lanes (Stratford)')
            
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                allstarlanes_bowling.scrape_allstarlanes,
                venue_name,
                'London',
                guests,
                guests,
                target_date,
                location,
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
def scrape_lucky_strike_task(self, guests, target_date, task_id=None, location='chelsea_piers'):
    """Lucky Strike scraper as Celery task"""
    with app.app_context():
        try:
            from scrapers.lucky_strike import LUCKY_STRIKE_VENUE_NAMES
            venue_name = LUCKY_STRIKE_VENUE_NAMES.get(location, 'Lucky Strike (Chelsea Piers)')
            
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                lambda g, d: lucky_strike.scrape_lucky_strike(g, d, location),
                venue_name,
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
                easybowl.scrape_easybowl,
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


@celery_app.task(bind=True, name='app.scrape_tsquaredsocial_task')
def scrape_tsquaredsocial_task(self, guests, target_date, task_id=None, selected_time=None):
    """T-Squared Social scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape T-Squared Social...', current_venue='T-Squared Social')
            
            slots_saved = run_scraper_and_save_to_db(
                tsquaredsocial.scrape_tsquaredsocial,
                'T-Squared Social',
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


@celery_app.task(bind=True, name='app.scrape_hijingo_task')
def scrape_hijingo_task(self, guests, target_date, task_id=None):
    """Hijingo scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Hijingo...', current_venue='Hijingo')
            
            slots_saved = run_scraper_and_save_to_db(
                hijingo.scrape_hijingo,
                'Hijingo',
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


@celery_app.task(bind=True, name='app.scrape_pingpong_task')
def scrape_pingpong_task(self, guests, target_date, task_id=None):
    """Bounce scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Bounce...', current_venue='Bounce')
            
            slots_saved = run_scraper_and_save_to_db(
                pingpong.scrape_pingpong,
                'Bounce',
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


def scrape_daysmart_chelsea_wrapper(guests, target_date):
    """Wrapper function for DaySmart Chelsea scraper - only works for 2 guests"""
    if guests != 2:
        logger = logging.getLogger(__name__)
        logger.info(f"[DaySmart Chelsea] Skipping scrape - only supports 2 guests, got {guests}")
        return []
    return daysmart.scrape_daysmart_chelsea(target_date)


@celery_app.task(bind=True, name='app.scrape_daysmart_chelsea_task')
def scrape_daysmart_chelsea_task(self, guests, target_date, task_id=None):
    """DaySmart Chelsea scraper as Celery task - only works for 2 guests"""
    with app.app_context():
        try:
            logger = logging.getLogger(__name__)
            
            # Check if guests is 2, if not skip gracefully
            if guests != 2:
                if task_id:
                    update_task_status(task_id, status='SUCCESS', progress=f'Skipped - Chelsea Piers Golf only supports 2 guests (requested: {guests})', total_slots=0)
                logger.info(f"[DaySmart Chelsea] Skipping scrape - only supports 2 guests, got {guests}")
                return {'status': 'success', 'slots_found': 0, 'message': f'Chelsea Piers Golf only supports 2 guests (requested: {guests})'}
            
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Chelsea Piers Golf...', current_venue='Chelsea Piers Golf')
            
            slots_saved = run_scraper_and_save_to_db(
                scrape_daysmart_chelsea_wrapper,
                'Chelsea Piers Golf',
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
                fair_game.scrape_fair_game_canary_wharf,
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
                fair_game.scrape_fair_game_city,
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
            venue_name = f'Clays Bar ({location or "Canary Wharf"})'
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                clays_bar.scrape_clays_bar,
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
            venue_name = f'Puttshack ({location or "Bank"})'
            if task_id:
                update_task_status(task_id, status='STARTED', progress=f'Starting to scrape {venue_name}...', current_venue=venue_name)
            
            slots_saved = run_scraper_and_save_to_db(
                puttshack.scrape_puttshack,
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
def scrape_flight_club_darts_task(self, guests, target_date, venue_id=None, task_id=None):
    """Flight Club Darts scraper as Celery task - scrapes ALL 4 locations in one task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Flight Club Darts (all 4 locations)...', current_venue='Flight Club Darts')
            
            # Call scraper without venue_id to get all locations
            # The scraper will return results with different venue names for each location
            slots_saved = run_scraper_and_save_to_db(
                flight_club_darts.scrape_flight_club_darts,
                'Flight Club Darts',  # Base venue name, but results will have specific names
                'London',
                guests,
                guests,
                target_date,
                venue_id,  # Pass None to scrape all, or specific venue_id for backward compatibility
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots across all 4 locations', total_slots=slots_saved)
            
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
                f1_arcade.scrape_f1_arcade,
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
            raise e


@celery_app.task(bind=True, name='app.scrape_topgolf_chigwell_task')
def scrape_topgolf_chigwell_task(self, guests, target_date, task_id=None, start_time=None):
    """Topgolf Chigwell scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Topgolf Chigwell...', current_venue='Topgolf Chigwell')
            
            slots_saved = run_scraper_and_save_to_db(
                topgolfchigwell.scrape_topgolf_chigwell,
                'Topgolf Chigwell',
                'London',
                guests,
                guests,
                target_date,
                start_time,
                task_id=task_id
            )
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_puttery_task')
def scrape_puttery_task(self, guests, target_date, task_id=None):
    """Puttery NYC scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Puttery (NYC)...', current_venue='Puttery (NYC)')
            
            slots_saved = run_scraper_and_save_to_db(
                puttery.scrape_puttery,
                'Puttery (NYC)',
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


@celery_app.task(bind=True, name='app.scrape_kick_axe_task')
def scrape_kick_axe_task(self, guests, target_date, task_id=None):
    """Kick Axe Brooklyn scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Kick Axe (Brooklyn)...', current_venue='Kick Axe (Brooklyn)')
            
            slots_saved = run_scraper_and_save_to_db(
                kick_axe.scrape_kick_axe,
                'Kick Axe (Brooklyn)',
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


@celery_app.task(bind=True, name='app.scrape_venue_task')
def scrape_venue_task(self, guests, target_date, website, task_id=None, lawn_club_option=None, lawn_club_time=None, lawn_club_duration=None, spin_time=None, clays_location=None, puttshack_location=None, f1_experience=None):
    """Celery task wrapper for scraping a single venue"""
    with app.app_context():
        try:
            logger = logging.getLogger(__name__)
            
            # Clean up old slots before scraping (only once per task)
            cleanup_old_slots()
            
            logger.info(f"[VENUE_TASK] Starting scrape for {website} (date: {target_date}, guests: {guests})")
            
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
            
            city = 'NYC' if 'nyc' in website or website in NYC_VENUES else 'London'
            venue_name_map = {
                'swingers_nyc': 'Swingers (NYC)',
                'swingers_london': 'Swingers (London)',
                'electric_shuffle_nyc': 'Electric Shuffle (NYC)',
                'electric_shuffle_london': 'Electric Shuffle (London)',
                'lawn_club_nyc_indoor_gaming': 'Lawn Club (Indoor Gaming)',
                'lawn_club_nyc_curling_lawns': 'Lawn Club (Curling Lawns)',
                'lawn_club_nyc_croquet_lawns': 'Lawn Club (Croquet Lawns)',
                'spin_nyc': 'SPIN (NYC - Flatiron)',
                'spin_nyc_midtown': 'SPIN (NYC - Midtown)',
                'five_iron_golf_nyc_fidi': 'Five Iron Golf (NYC - FiDi)',
                'five_iron_golf_nyc_flatiron': 'Five Iron Golf (NYC - Flatiron)',
                'five_iron_golf_nyc_grand_central': 'Five Iron Golf (NYC - Grand Central)',
                'five_iron_golf_nyc_herald_square': 'Five Iron Golf (NYC - Herald Square)',
                'five_iron_golf_nyc_long_island_city': 'Five Iron Golf (NYC - Long Island City)',
                'five_iron_golf_nyc_upper_east_side': 'Five Iron Golf (NYC - Upper East Side)',
                'five_iron_golf_nyc_rockefeller_center': 'Five Iron Golf (NYC - Rockefeller Center)',
                'lucky_strike_nyc': 'Lucky Strike (Chelsea Piers)',
                'lucky_strike_nyc_times_square': 'Lucky Strike (Times Square)',
                'easybowl_nyc': 'Easybowl (NYC)',
                'tsquaredsocial_nyc': 'T-Squared Social',
                'daysmart_chelsea': 'Chelsea Piers Golf',
                'fair_game_canary_wharf': 'Fair Game (Canary Wharf)',
                'fair_game_city': 'Fair Game (City)',
                'clays_bar': f'Clays Bar ({clays_location or "Canary Wharf"})',
                'puttshack': f'Puttshack ({puttshack_location or "Bank"})',
                'flight_club_darts': 'Flight Club Darts',
                'f1_arcade': 'F1 Arcade',
                'topgolf_chigwell': 'Topgolf Chigwell',
                'hijingo': 'Hijingo',
                'pingpong': 'Bounce',
                'puttery_nyc': 'Puttery (NYC)',
                'kick_axe_brooklyn': 'Kick Axe (Brooklyn)'
            }
            
            # Handle Lawn Club, Five Iron Golf, and All Star Lanes venue names dynamically
            if website.startswith('lawn_club_nyc_'):
                from scrapers.lawn_club import LAWN_CLUB_VENUE_NAMES
                option = website.replace('lawn_club_nyc_', '')
                venue_name = LAWN_CLUB_VENUE_NAMES.get(option, 'Lawn Club (Indoor Gaming)')
            elif website.startswith('five_iron_golf_nyc_'):
                from scrapers.five_iron_golf import FIVE_IRON_VENUE_NAMES
                location = website.replace('five_iron_golf_nyc_', '')
                venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf (NYC - FiDi)')
            elif website.startswith('allstarlanes_'):
                from scrapers.allstarlanes_bowling import ALLSTARLANES_VENUE_NAMES
                location = website.replace('allstarlanes_', '')
                venue_name = ALLSTARLANES_VENUE_NAMES.get(location, 'All Star Lanes')
            else:
                venue_name = venue_name_map.get(website, website.replace('_', ' ').title())
            
            if website == 'swingers_nyc':
                result = scrape_swingers_task(guests, target_date, task_id)
            elif website == 'swingers_london':
                result = scrape_swingers_uk_task(guests, target_date, task_id)
            elif website == 'electric_shuffle_nyc':
                if not target_date:
                    raise ValueError("Electric Shuffle NYC requires a specific target date")
                result = scrape_electric_shuffle_task(guests, target_date, task_id)
            elif website == 'electric_shuffle_london':
                if not target_date:
                    raise ValueError("Electric Shuffle London requires a specific target date")
                result = scrape_electric_shuffle_london_task(guests, target_date, task_id)
            elif website.startswith('lawn_club_nyc_'):
                if not target_date:
                    raise ValueError("Lawn Club NYC requires a specific target date")
                # Extract option from website name (e.g., 'lawn_club_nyc_indoor_gaming' -> 'indoor_gaming')
                option = website.replace('lawn_club_nyc_', '')
                from scrapers.lawn_club import LAWN_CLUB_VENUE_NAMES
                venue_name = LAWN_CLUB_VENUE_NAMES.get(option, 'Lawn Club (Indoor Gaming)')
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_lawn_club_task with option {option}")
                result = scrape_lawn_club_task(guests, target_date, option, task_id, lawn_club_time, lawn_club_duration)
            elif website == 'spin_nyc':
                if not target_date:
                    raise ValueError("SPIN NYC requires a specific target date")
                result = scrape_spin_task(guests, target_date, task_id, spin_time, location='flatiron')
            elif website.startswith('spin_nyc_'):
                if not target_date:
                    raise ValueError("SPIN NYC requires a specific target date")
                # Extract location from website name (e.g., 'spin_nyc_midtown' -> 'midtown')
                location = website.replace('spin_nyc_', '')
                from scrapers.spin import SPIN_VENUE_NAMES
                venue_name = SPIN_VENUE_NAMES.get(location, 'SPIN (NYC - Flatiron)')
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_spin_task with location {location}")
                result = scrape_spin_task(guests, target_date, task_id, spin_time, location=location)
            elif website.startswith('five_iron_golf_nyc_'):
                if not target_date:
                    raise ValueError("Five Iron Golf NYC requires a specific target date")
                # Extract location from website name (e.g., 'five_iron_golf_nyc_fidi' -> 'fidi')
                location = website.replace('five_iron_golf_nyc_', '')
                from scrapers.five_iron_golf import FIVE_IRON_VENUE_NAMES
                venue_name = FIVE_IRON_VENUE_NAMES.get(location, 'Five Iron Golf (NYC - FiDi)')
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_five_iron_golf_task with location {location}")
                result = scrape_five_iron_golf_task(guests, target_date, task_id, location)
            elif website.startswith('lucky_strike_nyc'):
                if not target_date:
                    raise ValueError("Lucky Strike NYC requires a specific target date")
                # Extract location from website name (e.g., 'lucky_strike_nyc_times_square' -> 'times_square', 'lucky_strike_nyc' -> 'chelsea_piers')
                if website == 'lucky_strike_nyc':
                    location = 'chelsea_piers'
                elif website == 'lucky_strike_nyc_times_square':
                    location = 'times_square'
                else:
                    location = 'chelsea_piers'  # default
                from scrapers.lucky_strike import LUCKY_STRIKE_VENUE_NAMES
                venue_name = LUCKY_STRIKE_VENUE_NAMES.get(location, 'Lucky Strike (Chelsea Piers)')
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_lucky_strike_task with location {location}")
                result = scrape_lucky_strike_task(guests, target_date, task_id, location)
            elif website == 'easybowl_nyc':
                if not target_date:
                    raise ValueError("Easybowl NYC requires a specific target date")
                result = scrape_easybowl_task(guests, target_date, task_id)
            elif website == 'tsquaredsocial_nyc':
                if not target_date:
                    raise ValueError("T-Squared Social requires a specific target date")
                result = scrape_tsquaredsocial_task(guests, target_date, task_id)
            elif website == 'daysmart_chelsea':
                if not target_date:
                    raise ValueError("Chelsea Piers Golf requires a specific target date")
                result = scrape_daysmart_chelsea_task(guests, target_date, task_id)
            elif website == 'fair_game_canary_wharf':
                if not target_date:
                    raise ValueError("Fair Game (Canary Wharf) requires a specific target date")
                result = scrape_fair_game_canary_wharf_task(guests, target_date, task_id)
            elif website == 'fair_game_city':
                if not target_date:
                    raise ValueError("Fair Game (City) requires a specific target date")
                result = scrape_fair_game_city_task(guests, target_date, task_id)
            elif website == 'clays_bar':
                if not target_date:
                    raise ValueError("Clays Bar requires a specific target date")
                location = clays_location or "Canary Wharf"
                result = scrape_clays_bar_task(location, guests, target_date, task_id)
            elif website == 'puttshack':
                if not target_date:
                    raise ValueError("Puttshack requires a specific target date")
                location = puttshack_location or "Bank"
                result = scrape_puttshack_task(location, guests, target_date, task_id)
            elif website == 'flight_club_darts':
                if not target_date:
                    raise ValueError("Flight Club Darts requires a specific target date")
                # Scrape all 4 locations in one task - venue_id=None means scrape all
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_flight_club_darts_task to scrape all 4 locations")
                result = scrape_flight_club_darts_task(guests, target_date, None, task_id)
            elif website == 'f1_arcade':
                if not target_date:
                    raise ValueError("F1 Arcade requires a specific target date")
                experience = f1_experience or "Team Racing"
                result = scrape_f1_arcade_task(guests, target_date, experience, task_id)
            elif website == 'topgolf_chigwell':
                if not target_date:
                    raise ValueError("Topgolf Chigwell requires a specific target date")
                result = scrape_topgolf_chigwell_task(guests, target_date, task_id)
            elif website == 'hijingo':
                if not target_date:
                    raise ValueError("Hijingo requires a specific target date")
                result = scrape_hijingo_task(guests, target_date, task_id)
            elif website == 'pingpong':
                if not target_date:
                    raise ValueError("Bounce requires a specific target date")
                result = scrape_pingpong_task(guests, target_date, task_id)
            elif website == 'puttery_nyc':
                if not target_date:
                    raise ValueError("Puttery (NYC) requires a specific target date")
                result = scrape_puttery_task(guests, target_date, task_id)
            elif website == 'kick_axe_brooklyn':
                if not target_date:
                    raise ValueError("Kick Axe (Brooklyn) requires a specific target date")
                result = scrape_kick_axe_task(guests, target_date, task_id)
            elif website.startswith('allstarlanes_'):
                if not target_date:
                    raise ValueError("All Star Lanes requires a specific target date")
                # Extract location from website name (e.g., 'allstarlanes_stratford' -> 'stratford')
                location = website.replace('allstarlanes_', '')
                from scrapers.allstarlanes_bowling import ALLSTARLANES_VENUE_NAMES
                venue_name = ALLSTARLANES_VENUE_NAMES.get(location, 'All Star Lanes (Stratford)')
                logger.info(f"[VENUE_TASK] {website}: Calling scrape_allstarlanes_task with location {location}")
                result = scrape_allstarlanes_task(guests, target_date, task_id, location)
            else:
                logger.error(f"[VENUE_TASK] {website}: Unknown website!")
                raise ValueError(f"Unknown website: {website}")
            
            slots_found = result.get("slots_found", 0) if isinstance(result, dict) else 0
            logger.info(f"[VENUE_TASK] {website}: Completed scraping, found {slots_found} slots")
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Scraping completed! Found {slots_found} slots')
            
            return result
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"[VENUE_TASK] {website}: Error during scraping: {e}", exc_info=True)
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e


@celery_app.task(bind=True, name='app.scrape_all_venues_task')
def scrape_all_venues_task(self, city, guests, target_date, task_id=None, options=None):
    """Scrape all venues in a city for one or more dates simultaneously using Celery chord"""
    with app.app_context():
        import time
        start_time = time.time()
        
        try:
            logger = logging.getLogger(__name__)
            
            # Clean up old slots before starting a new scraping session
            cleanup_old_slots()
            
            if isinstance(target_date, str):
                target_dates = [target_date]
            elif isinstance(target_date, list):
                target_dates = target_date
            else:
                raise ValueError(f"target_date must be a string or list, got {type(target_date)}")
            
            if not task_id:
                task_id = self.request.id
            
            task = ScrapingTask.query.filter_by(task_id=task_id).first()
            if not task:
                from datetime import date
                city_lower = city.lower()
                today = date.today()
                
                if len(target_dates) == 1:
                    target_date_obj = datetime.strptime(target_dates[0], "%Y-%m-%d").date()
                    if target_date_obj == today:
                        date_type = 'today'
                    elif target_date_obj == today + timedelta(days=1):
                        date_type = 'tomorrow'
                    else:
                        date_type = target_date_obj.isoformat()
                else:
                    first_date = datetime.strptime(target_dates[0], "%Y-%m-%d").date()
                    last_date = datetime.strptime(target_dates[-1], "%Y-%m-%d").date()
                    date_type = f'{len(target_dates)}days_{first_date.isoformat()}_{last_date.isoformat()}'
                
                if city_lower in ['nyc', 'new york']:
                    website_name = f'all_nyc_{date_type}'
                elif city_lower == 'london':
                    website_name = f'all_london_{date_type}'
                else:
                    website_name = f'all_{city_lower.replace(" ", "_")}_{date_type}'
                
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
            else:
                task.status = 'STARTED'
                task.progress = f'Starting to scrape all {city} venues for {len(target_dates)} date(s)...'
                db.session.commit()
            
            if city.lower() == 'nyc' or city.lower() == 'new york':
                venues = NYC_VENUES
                city_name = 'NYC'
            elif city.lower() == 'london':
                venues = LONDON_VENUES
                city_name = 'London'
            else:
                raise ValueError(f"Unknown city: {city}")
            
            options = options or {}
            
            venue_tasks = []
            for venue in venues:
                for date_str in target_dates:
                    venue_task_id = f"{task_id}_{venue}_{date_str}" if task_id else None
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
            
            total_tasks = len(venue_tasks)
            
            callback = update_parent_task_duration.s(parent_task_id=task_id, total_tasks=total_tasks)
            job = chord(venue_tasks)(callback)
            
            task.status = 'SUBMITTED'
            task.progress = f'Submitted {total_tasks} scraping tasks for {len(venues)} {city_name} venues across {len(target_dates)} dates. Tasks are running in parallel.'
            db.session.commit()
            
            return {
                'status': 'submitted', 
                'tasks_submitted': total_tasks,
                'venues': len(venues), 
                'dates': len(target_dates),
                'message': f'Submitted {total_tasks} scraping tasks. Results will be saved to database as tasks complete.'
            }
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"[SCRAPE_ALL] Error in scrape_all_venues_task: {e}", exc_info=True)
            
            end_time = time.time()
            duration_seconds = end_time - start_time
            
            task = ScrapingTask.query.filter_by(task_id=task_id).first()
            if task:
                task.duration_seconds = duration_seconds
                task.completed_at = datetime.utcnow()
                task.status = 'FAILURE'
                task.error = str(e)
                db.session.commit()
            raise e


@celery_app.task(bind=True, name='app.update_parent_task_duration')
def update_parent_task_duration(self, results, parent_task_id=None, total_tasks=None):
    """Callback task to update parent task duration when all child tasks complete"""
    with app.app_context():
        import time
        logger = logging.getLogger(__name__)
        
        try:
            if not parent_task_id:
                parent_task_id = self.request.kwargs.get('parent_task_id')
            if not total_tasks:
                total_tasks = self.request.kwargs.get('total_tasks')
            
            if not parent_task_id:
                logger.error(f"[DURATION_CALLBACK] No parent_task_id provided!")
                return
            
            total_tasks = total_tasks or (len(results) if results else 0)
            
            task = ScrapingTask.query.filter_by(task_id=parent_task_id).first()
            if not task:
                logger.error(f"[DURATION_CALLBACK] Parent task {parent_task_id} not found!")
                return
            
            if task.created_at:
                end_time = datetime.utcnow()
                duration_timedelta = end_time - task.created_at
                duration_seconds = duration_timedelta.total_seconds()
                
                successful = 0
                failed = 0
                if results:
                    for r in results:
                        if hasattr(r, 'successful'):
                            try:
                                if r.successful():
                                    successful += 1
                                else:
                                    failed += 1
                            except:
                                failed += 1
                        elif r is not None:
                            successful += 1
                        else:
                            failed += 1
                else:
                    successful = total_tasks
                
                task.duration_seconds = duration_seconds
                task.completed_at = end_time
                task.status = 'SUCCESS'
                task.progress = f'All {total_tasks} scraping tasks completed! ({successful} successful, {failed} failed)'
                db.session.commit()
        except Exception as e:
            logger.error(f"[DURATION_CALLBACK] Error updating parent task duration: {e}", exc_info=True)


@celery_app.task(bind=True, name='app.trigger_next_refresh_cycle')
def trigger_next_refresh_cycle(self, results=None):
    """Callback task to trigger the next refresh cycle after current cycle completes"""
    with app.app_context():
        logger = logging.getLogger(__name__)
        try:
            logger.info("[REFRESH] Current cycle completed. Starting next cycle...")
            # Trigger the next refresh cycle
            refresh_all_venues_task.delay()
            logger.info("[REFRESH] Next refresh cycle triggered successfully")
        except Exception as e:
            logger.error(f"[REFRESH] Error triggering next cycle: {e}", exc_info=True)
            # Don't raise - we don't want to break the chain if there's an error


@celery_app.task(bind=True, name='app.refresh_all_venues_task')
def refresh_all_venues_task(self):
    """Periodic task to refresh all venues for guests 2-8, for 30 days in one cycle.
    Creates tasks at venue × guest × date level.
    Note: daysmart_chelsea only supports 2 guests, so tasks for guests 3-8 are skipped for that venue.
    Tasks are shuffled to interleave different venues and reduce IP blocking risk.
    Automatically triggers the next cycle when all tasks complete."""
    with app.app_context():
        try:
            from datetime import date
            import random
            logger = logging.getLogger(__name__)
            
            today = date.today()
            dates_to_refresh = [today + timedelta(days=i) for i in range(30)]
            date_strings = [d.isoformat() for d in dates_to_refresh]
            
            # Combine all venues from both cities
            all_venues = NYC_VENUES + LONDON_VENUES
            logger.info(f"[REFRESH] Total venues: {len(all_venues)} (NYC: {len(NYC_VENUES)}, London: {len(LONDON_VENUES)})")
            logger.info(f"[REFRESH] NYC venues: {NYC_VENUES}")
            logger.info(f"[REFRESH] London venues: {LONDON_VENUES}")
            
            # Scrape for guests 2 through 8
            guest_counts = list(range(2, 9))  # [2, 3, 4, 5, 6, 7, 8]
            
            # Venues that only support specific guest counts
            # daysmart_chelsea only supports 2 guests
            VENUE_GUEST_RESTRICTIONS = {
                'daysmart_chelsea': [2]  # Only scrape for 2 guests
            }
            
            # Create tasks at venue × guest × date level (not grouped by venue)
            all_tasks = []
            venue_task_counts = {}  # Track tasks per venue for verification
            
            for venue in all_venues:
                # Get allowed guest counts for this venue
                allowed_guests = VENUE_GUEST_RESTRICTIONS.get(venue, guest_counts)
                venue_task_counts[venue] = 0
                
                for guests in guest_counts:
                    # Skip if this venue doesn't support this guest count
                    if guests not in allowed_guests:
                        continue
                    
                    for date_str in date_strings:
                        all_tasks.append(
                            scrape_venue_task.s(
                                guests=guests,
                                target_date=date_str,
                                website=venue,
                                task_id=None,
                                lawn_club_option=None,
                                lawn_club_time=None,
                                lawn_club_duration=None,
                                spin_time=None,
                                clays_location=None,
                                puttshack_location=None,
                                f1_experience=None
                            )
                        )
                        venue_task_counts[venue] += 1
            
            # Verify all expected venues are included in tasks
            venues_with_tasks = [v for v, count in venue_task_counts.items() if count > 0]
            missing_venues = set(all_venues) - set(venues_with_tasks)
            if missing_venues:
                logger.warning(f"[REFRESH] WARNING: Some venues have no tasks: {missing_venues}")
            else:
                logger.info(f"[REFRESH] ✓ All {len(all_venues)} venues have tasks created")
            
            # Log task counts for key venues
            key_venues = ['hijingo', 'puttery_nyc', 'kick_axe_brooklyn', 'pingpong', 'daysmart_chelsea', 'tsquaredsocial_nyc', 'topgolf_chigwell']
            key_venue_counts = [(v, venue_task_counts.get(v, 0)) for v in key_venues if v in all_venues]
            logger.info(f"[REFRESH] Task counts for key venues: {key_venue_counts}")
            logger.info(f"[REFRESH] Total tasks created: {len(all_tasks)}")
            
            # Shuffle all tasks to interleave different venues and reduce IP blocking risk
            logger.info(f"[REFRESH] Shuffling {len(all_tasks)} tasks to interleave different venues and reduce IP blocking risk...")
            random.shuffle(all_tasks)
            
            # Verify shuffling worked by sampling venues from first tasks
            # Extract venue from task signatures (Celery signatures store kwargs)
            first_venues_sample = []
            for i, task in enumerate(all_tasks[:30]):
                try:
                    # Celery signature objects have kwargs attribute
                    if hasattr(task, 'kwargs') and 'website' in task.kwargs:
                        first_venues_sample.append(task.kwargs['website'])
                    elif hasattr(task, 'args') and len(task.args) >= 3:
                        # Fallback: website is 3rd positional arg (guests, target_date, website)
                        first_venues_sample.append(task.args[2])
                except (AttributeError, IndexError):
                    pass
                if len(first_venues_sample) >= 20:
                    break
            
            if first_venues_sample:
                unique_first_venues = len(set(first_venues_sample))
                logger.info(f"[REFRESH] ✓ Tasks shuffled successfully. First {len(first_venues_sample)} tasks contain {unique_first_venues} unique venues")
                logger.info(f"[REFRESH] Sample of shuffled venues: {first_venues_sample[:10]}")
            else:
                logger.warning(f"[REFRESH] Could not verify shuffling (could not extract venue info from task signatures)")
            
            total_tasks = len(all_tasks)
            total_operations = total_tasks  # Each task is one operation
            
            # Calculate expected distribution
            # Most venues support all guest counts, but daysmart_chelsea only supports 2
            venues_with_all_guests = len(all_venues) - len(VENUE_GUEST_RESTRICTIONS)
            venues_with_restrictions = len(VENUE_GUEST_RESTRICTIONS)
            expected_per_guest_all_venues = venues_with_all_guests * len(date_strings)
            expected_per_guest_restricted = sum(
                len(restricted_guests) * len(date_strings)
                for restricted_guests in VENUE_GUEST_RESTRICTIONS.values()
            )
            expected_total = expected_per_guest_all_venues * len(guest_counts) + expected_per_guest_restricted
            
            logger.info(f"[REFRESH] Venue guest restrictions: {VENUE_GUEST_RESTRICTIONS}")
            logger.info(f"[REFRESH] Expected tasks: {expected_total} (most venues: {venues_with_all_guests} × {len(guest_counts)} guests × {len(date_strings)} dates = {expected_per_guest_all_venues * len(guest_counts)}, restricted venues: {expected_per_guest_restricted})")
            
            # Verify task creation and counts
            logger.info(f"[REFRESH] Total scraping operations: {total_operations}")
            logger.info(f"[REFRESH] Guest counts included: {guest_counts}")
            if total_tasks != expected_total:
                logger.warning(f"[REFRESH] Task count mismatch: expected {expected_total}, got {total_tasks}")
            else:
                logger.info(f"[REFRESH] Task count matches expected: {total_tasks}")
            logger.info(f"[REFRESH] IMPORTANT: All tasks are shuffled before submission. Execution order depends on worker concurrency and queue processing.")
            
            # Use chord to wait for all tasks to complete, then trigger next cycle
            callback = trigger_next_refresh_cycle.s()
            job = chord(all_tasks)(callback)
            
            logger.info(f"[REFRESH] All {total_tasks} tasks submitted (shuffled). Next cycle will start automatically when this cycle completes.")
            
            return {
                'status': 'submitted', 
                'dates_refreshed': len(dates_to_refresh), 
                'venues': len(all_venues),
                'guest_counts': guest_counts,
                'tasks_created': total_tasks,
                'total_operations': total_operations,
                'shuffled': True,
                'next_cycle': 'will_start_automatically'
            }
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"[REFRESH] Error in refresh_all_venues_task: {e}", exc_info=True)
            raise e


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8010)

