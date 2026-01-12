"""
All Star Lanes – Bowling slots scraper (UI-accurate)
"""

import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://allstarlanes-dmn-production.standard.aws.prop.cm/v1"

# -------------------------------------------------
# FRONTEND-CONFIRMED CONSTANTS for Stratford
# -------------------------------------------------
VENUE_ID_Stratford = "512b203bd5d190d2978ca5df"

# ✅ REAL Bowling bookingType (from your curl)
BOOKING_TYPE_BOWLING_Stratford = "690ce403519a2958fb5dfe84"


# -------------------------------------------------
# FRONTEND-CONFIRMED CONSTANTS for Holborn
# -------------------------------------------------

VENUE_ID_Holborn = "512b2039d5d190d2978ca5a9"
BOOKING_TYPE_BOWLING_Holborn = "690e393c418a8165ff31332d"


# -------------------------------------------------
# FRONTEND-CONFIRMED CONSTANTS for White City
# -------------------------------------------------

VENUE_ID_White = "5acb7e997b71be7b0c1d6af6"
BOOKING_TYPE_BOWLING_White = "690ce403519a2958fb5dfe84"


# -------------------------------------------------
# FRONTEND-CONFIRMED CONSTANTS for Brick Lane
# -------------------------------------------------

VENUE_ID_Brick = "512b201cd5d190d2978ca211"
BOOKING_TYPE_BOWLING_Brick = "690f68b1933683061c41a8f7"

# ✅ REAL frontend duration
DEFAULT_DURATION = 30  # minutes

# Venue name mappings for each location
ALLSTARLANES_VENUE_NAMES = {
    'stratford': 'All Star Lanes (Stratford)',
    'holborn': 'All Star Lanes (Holborn)',
    'white_city': 'All Star Lanes (White City)',
    'brick_lane': 'All Star Lanes (Brick Lane)'
}

# Venue group constant (same for all locations)
VENUE_GROUP = "514ada610df690b6770000d7"


def generate_booking_url(venue_id, booking_type, guests, date, time, duration):
    """Generate booking URL with all required parameters"""
    from urllib.parse import urlencode, quote
    base_url = "https://bookings.designmynight.com/book"
    params = {
        'venue_group': VENUE_GROUP,
        'venue_id': venue_id,
        'type': booking_type,
        'num_people': guests,
        'date': date,
        'time': quote(time),  # URL encode time (12:00 → 12%3A00)
        'duration': duration,
        'source': 'partner',
        'return_url': 'https://www.allstarlanes.co.uk/booking/booking-thanks'
    }
    return f"{base_url}?{urlencode(params)}"


def calculate_duration_standard(guests):
    """
    Calculate duration for Stratford, Holborn, and White City
    - 2-7 guests: guests * 10
    - 8 guests: 40 mins
    - 9 guests: 50 mins
    """
    guests = int(guests)
    if guests >= 2 and guests <= 7:
        return guests * 10
    elif guests == 8:
        return 40
    elif guests == 9:
        return 50
    else:
        # Default fallback
        return guests * 10


def calculate_duration_brick_lane(guests):
    """
    Calculate duration for Brick Lane (all durations doubled)
    - 2-7 guests: guests * 20
    - 8 guests: 80 mins
    - 9 guests: 100 mins
    """
    guests = int(guests)
    if guests >= 2 and guests <= 7:
        return guests * 20
    elif guests == 8:
        return 80
    elif guests == 9:
        return 100
    else:
        # Default fallback
        return guests * 20


def scrape_allstarlanes_Stratford(guests, target_date, start_time=None):
    """
    Scrape Bowling slots for All Star Lanes
    Signature compatible with test_scrapers.py
    """

    results = []

    duration = calculate_duration_standard(guests)
    params = {
        "bookingType": BOOKING_TYPE_BOWLING_Stratford,
        "date": target_date,
        "numPeople": int(guests),
        "duration": duration,
    }

    url = f"{BASE_URL}/venue/{VENUE_ID_Stratford}/timeslots"

    # Log the exact URL being requested
    from urllib.parse import urlencode
    full_url = f"{url}?{urlencode(params)}"
    logger.info(f"[Stratford] Making request to: {full_url}")

    response = requests.get(url, params=params, timeout=15)
    
    logger.info(f"[Stratford] Response status: {response.status_code}")

    # Graceful empty handling
    if response.status_code == 400:
        logger.warning(
            f"[Stratford] No bowling availability for {target_date} "
            f"(guests={guests}, duration={duration})"
        )
        return []

    response.raise_for_status()

    payload = response.json()
    timeslots = payload.get("timeslots", [])

    for slot in timeslots:
        slot_time = slot.get("time")
        if not slot_time:
            continue

        if start_time and slot_time != start_time:
            continue

        start_dt = datetime.strptime(
            f"{target_date} {slot_time}",
            "%Y-%m-%d %H:%M"
        )
        end_dt = start_dt + timedelta(minutes=DEFAULT_DURATION)
        
        # Generate dynamic booking URL
        booking_url = generate_booking_url(
            venue_id=VENUE_ID_Stratford,
            booking_type=BOOKING_TYPE_BOWLING_Stratford,
            guests=int(guests),
            date=target_date,
            time=slot_time,  # Use original time format (HH:MM)
            duration=duration
        )

        results.append({
            "date": target_date,
            "time": start_dt.strftime("%I:%M %p"),
            "end_time": end_dt.strftime("%I:%M %p"),
            "availability": f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}",
            "duration": f"{DEFAULT_DURATION} minutes",
            "guests": guests,
            "status": "Available",
            "timestamp": datetime.now().isoformat(),
            "website": ALLSTARLANES_VENUE_NAMES['stratford'],
            "booking_url": booking_url,
        })
    
    logger.info(f"[Stratford] Processed {len(results)} available slots")

    return results



def scrape_allstarlanes_Holborn(guests, target_date, start_time=None):
    """
    Scrape Bowling slots for All Star Lanes
    Signature compatible with test_scrapers.py
    """

    results = []

    duration = calculate_duration_standard(guests)
    params = {
        "bookingType": BOOKING_TYPE_BOWLING_Holborn,
        "date": target_date,
        "numPeople": int(guests),
        "duration": duration,
    }

    url = f"{BASE_URL}/venue/{VENUE_ID_Holborn}/timeslots"

    # Log the exact URL being requested
    from urllib.parse import urlencode
    full_url = f"{url}?{urlencode(params)}"
    logger.info(f"[Holborn] Making request to: {full_url}")

    response = requests.get(url, params=params, timeout=15)
    
    logger.info(f"[Holborn] Response status: {response.status_code}")

    # Graceful empty handling
    if response.status_code == 400:
        logger.warning(
            f"[Holborn] No bowling availability for {target_date} "
            f"(guests={guests}, duration={duration})"
        )
        return []

    response.raise_for_status()

    payload = response.json()
    timeslots = payload.get("timeslots", [])
    
    logger.info(f"[Holborn] Found {len(timeslots)} timeslots in response")

    for slot in timeslots:
        slot_time = slot.get("time")
        if not slot_time:
            continue

        if start_time and slot_time != start_time:
            continue

        start_dt = datetime.strptime(
            f"{target_date} {slot_time}",
            "%Y-%m-%d %H:%M"
        )
        end_dt = start_dt + timedelta(minutes=DEFAULT_DURATION)
        
        # Generate dynamic booking URL
        booking_url = generate_booking_url(
            venue_id=VENUE_ID_Holborn,
            booking_type=BOOKING_TYPE_BOWLING_Holborn,
            guests=int(guests),
            date=target_date,
            time=slot_time,  # Use original time format (HH:MM)
            duration=duration
        )

        results.append({
            "date": target_date,
            "time": start_dt.strftime("%I:%M %p"),
            "end_time": end_dt.strftime("%I:%M %p"),
            "availability": f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}",
            "duration": f"{DEFAULT_DURATION} minutes",
            "guests": guests,
            "status": "Available",
            "timestamp": datetime.now().isoformat(),
            "website": ALLSTARLANES_VENUE_NAMES['holborn'],
            "booking_url": booking_url,
        })
    
    logger.info(f"[Holborn] Processed {len(results)} available slots")

    return results



def scrape_allstarlanes_White_city(guests, target_date, start_time=None):
    """
    Scrape Bowling slots for All Star Lanes
    Signature compatible with test_scrapers.py
    """

    results = []

    duration = calculate_duration_standard(guests)
    params = {
        "bookingType": BOOKING_TYPE_BOWLING_White,
        "date": target_date,
        "numPeople": int(guests),
        "duration": duration,
    }

    url = f"{BASE_URL}/venue/{VENUE_ID_White}/timeslots"

    # Log the exact URL being requested
    from urllib.parse import urlencode
    full_url = f"{url}?{urlencode(params)}"
    logger.info(f"[White City] Making request to: {full_url}")

    response = requests.get(url, params=params, timeout=15)
    
    logger.info(f"[White City] Response status: {response.status_code}")

    # Graceful empty handling
    if response.status_code == 400:
        logger.warning(
            f"[White City] No bowling availability for {target_date} "
            f"(guests={guests}, duration={duration})"
        )
        return []

    response.raise_for_status()

    payload = response.json()
    timeslots = payload.get("timeslots", [])
    
    logger.info(f"[White City] Found {len(timeslots)} timeslots in response")

    for slot in timeslots:
        slot_time = slot.get("time")
        if not slot_time:
            continue

        if start_time and slot_time != start_time:
            continue

        start_dt = datetime.strptime(
            f"{target_date} {slot_time}",
            "%Y-%m-%d %H:%M"
        )
        end_dt = start_dt + timedelta(minutes=DEFAULT_DURATION)
        
        # Generate dynamic booking URL
        booking_url = generate_booking_url(
            venue_id=VENUE_ID_White,
            booking_type=BOOKING_TYPE_BOWLING_White,
            guests=int(guests),
            date=target_date,
            time=slot_time,  # Use original time format (HH:MM)
            duration=duration
        )

        results.append({
            "date": target_date,
            "time": start_dt.strftime("%I:%M %p"),
            "end_time": end_dt.strftime("%I:%M %p"),
            "availability": f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}",
            "duration": f"{DEFAULT_DURATION} minutes",
            "guests": guests,
            "status": "Available",
            "timestamp": datetime.now().isoformat(),
            "website": ALLSTARLANES_VENUE_NAMES['white_city'],
            "booking_url": booking_url,
        })
    
    logger.info(f"[White City] Processed {len(results)} available slots")

    return results



def scrape_allstarlanes_Brick_lane(guests, target_date, start_time=None):
    """
    Scrape Bowling slots for All Star Lanes
    Signature compatible with test_scrapers.py
    """

    results = []

    duration = calculate_duration_brick_lane(guests)
    params = {
        "bookingType": BOOKING_TYPE_BOWLING_Brick,
        "date": target_date,
        "numPeople": int(guests),
        "duration": duration,
    }

    url = f"{BASE_URL}/venue/{VENUE_ID_Brick}/timeslots"

    # Log the exact URL being requested
    from urllib.parse import urlencode
    full_url = f"{url}?{urlencode(params)}"
    logger.info(f"[Brick Lane] Making request to: {full_url}")

    response = requests.get(url, params=params, timeout=15)
    
    logger.info(f"[Brick Lane] Response status: {response.status_code}")

    # Graceful empty handling
    if response.status_code == 400:
        logger.warning(
            f"[Brick Lane] No bowling availability for {target_date} "
            f"(guests={guests}, duration={duration})"
        )
        return []

    response.raise_for_status()

    payload = response.json()
    timeslots = payload.get("timeslots", [])
    
    logger.info(f"[Brick Lane] Found {len(timeslots)} timeslots in response")

    for slot in timeslots:
        slot_time = slot.get("time")
        if not slot_time:
            continue

        if start_time and slot_time != start_time:
            continue

        start_dt = datetime.strptime(
            f"{target_date} {slot_time}",
            "%Y-%m-%d %H:%M"
        )
        end_dt = start_dt + timedelta(minutes=DEFAULT_DURATION)
        
        # Generate dynamic booking URL
        booking_url = generate_booking_url(
            venue_id=VENUE_ID_Brick,
            booking_type=BOOKING_TYPE_BOWLING_Brick,
            guests=int(guests),
            date=target_date,
            time=slot_time,  # Use original time format (HH:MM)
            duration=duration
        )

        results.append({
            "date": target_date,
            "time": start_dt.strftime("%I:%M %p"),
            "end_time": end_dt.strftime("%I:%M %p"),
            "availability": f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}",
            "duration": f"{DEFAULT_DURATION} minutes",
            "guests": guests,
            "status": "Available",
            "timestamp": datetime.now().isoformat(),
            "website": ALLSTARLANES_VENUE_NAMES['brick_lane'],
            "booking_url": booking_url,
        })
    
    logger.info(f"[Brick Lane] Processed {len(results)} available slots")

    return results


def scrape_allstarlanes(guests, target_date, location='stratford', start_time=None):
    """
    Unified scraper function for All Star Lanes
    Routes to appropriate location-specific scraper based on location parameter
    
    Args:
        guests: Number of guests
        target_date: Date in YYYY-MM-DD format
        location: Location identifier ('stratford', 'holborn', 'white_city', 'brick_lane')
        start_time: Optional specific start time to filter
    
    Returns:
        List of availability slots with venue-specific names
    """
    location_map = {
        'stratford': scrape_allstarlanes_Stratford,
        'holborn': scrape_allstarlanes_Holborn,
        'white_city': scrape_allstarlanes_White_city,
        'brick_lane': scrape_allstarlanes_Brick_lane,
    }
    
    scraper_func = location_map.get(location.lower())
    if not scraper_func:
        logger.error(f"Unknown location: {location}. Valid locations: {list(location_map.keys())}")
        return []
    
    # Call the appropriate scraper function
    results = scraper_func(guests, target_date, start_time)
    
    # Ensure venue name is set correctly (already set in individual functions, but double-check)
    venue_name = ALLSTARLANES_VENUE_NAMES.get(location.lower())
    if venue_name:
        for result in results:
            result['website'] = venue_name
    
    return results
