import json
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

BASE_URL = (
    "https://bookings.designmynight.com/api/v4/venues"
    "/512b203fd5d190d2978ca644/booking-availability"
)
COOKIE_REGION = {"Cookie": "current_region=london"}


def fetch_json(url: str, params: dict) -> dict:
    """Send GET request and return JSON or raise helpful error."""
    with requests.Session() as session:
        session.headers.update(COOKIE_REGION)
        response = session.get(url, params=params, timeout=10)

    if response.status_code != 200:
        raise RuntimeError(f"Request failed [{response.status_code}]: {response.text}")

    try:
        return response.json()
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON received: {response.text}")


def fetch_available_dates(num_people: int, start_date: str) -> list:
    """Fetch and return a list of valid available dates on or after start_date."""
    params = {
        "num_people": num_people,
        "fields": "date",
        "date": start_date,
        "source": "partner",
    }

    data = fetch_json(BASE_URL, params)
    suggested = data["payload"]["validation"]["date"]["suggestedValues"]

    # Filter to only include valid dates that are >= start_date
    valid_dates = [
        d["date"] 
        for d in suggested 
        if d.get("valid") and d["date"] >= start_date
    ]
    return valid_dates


def fetch_available_times(date: str, num_people: int, time_from: int) -> list:
    """Fetch valid booking times within a 2-hour range."""
    params = {
        "type": "5955253c91c098669b3202d3",
        "num_people": num_people,
        "date": date,
        "getOffers": "true",
        "time_from": f"{time_from}:00",
        "time_to": f"{time_from + 2}:59",
        "source": "partner",
        "partner_source": "undefined",
    }

    data = fetch_json(BASE_URL, params)
    suggested = data["payload"]["validation"]["time"]["suggestedValues"]

    return [
        t["time"]
        for t in suggested
        if t.get("valid") and t.get("action") == "accept"
    ]


def scrape_pingpong(guests, target_date):
    """
    Scrape Bounce availability slots
    :param guests: Number of guests (e.g., 4)
    :param target_date: Date in format "YYYY-MM-DD" (e.g., "2026-01-15")
    :return: List of slot dictionaries in app format
    """
    results = []
    
    try:
        logger.info(f"[Bounce] Starting scrape for {guests} guests on {target_date}")
        
        # Fetch available dates starting from target_date
        dates = fetch_available_dates(guests, target_date)
        
        if not dates:
            logger.info(f"[Bounce] No available dates found starting from {target_date}")
            return results
        
        logger.info(f"[Bounce] Found {len(dates)} available date(s)")
        
        # For each date, fetch all available times
        for date in dates:
            all_times = []
            
            # Check all time windows (12-14, 15-17, 18-20, 21-23)
            start_time = 12
            for window in range(4):
                try:
                    times = fetch_available_times(date, guests, start_time)
                    if times:
                        all_times.extend(times)
                except Exception as e:
                    logger.warning(f"[Bounce] Error fetching times for {date} window {start_time}:00-{start_time+2}:59: {e}")
                
                start_time += 3
            
            # Create slot entries for each time
            for time_str in sorted(all_times):
                # Construct booking URL with date, time, and guests
                # URL encode the time (e.g., "20:30" becomes "20%3A30")
                time_encoded = time_str.replace(':', '%3A')
                booking_url = (
                    f"https://bookings.designmynight.com/book?"
                    f"widget_version=2&"
                    f"venue_id=512b203fd5d190d2978ca644&"
                    f"venue_group=5536821278727915249864d6&"
                    f"type=5955253c91c098669b3202d3&"
                    f"num_people={guests}&"
                    f"date={date}&"
                    f"time={time_encoded}&"
                    f"duration=55&"
                    f"marketing_preferences=&"
                    f"tags=%7B%7D&"
                    f"source=partner&"
                    f"return_url=https%3A%2F%2Fwww.bouncepingpong.com%2Fapi%2Fbooking-confirmed%2F&"
                    f"return_method=post&"
                    f"gtm_account=Farringdon_booknow&"
                    f"locale=en-GB"
                )
                
                result_item = {
                    'date': date,
                    'time': time_str,
                    'price': 'Price not available',  # API doesn't provide price
                    'status': 'Available',
                    'website': 'Bounce',
                    'guests': guests,
                    'timestamp': datetime.now().isoformat(),
                    'booking_url': booking_url,
                }
                results.append(result_item)
        
        logger.info(f"[Bounce] Found {len(results)} available slots")
        return results
        
    except Exception as e:
        logger.error(f"[Bounce] Error during scraping: {str(e)}", exc_info=True)
        return results


def main():
    num_people = 4
    start_date = "2025-12-01"

    print(f"Checking availability starting at: {start_date}…\n")
    dates = fetch_available_dates(num_people, start_date)

    if not dates:
        print("❌ No valid dates returned.")
        return

    for date in dates:
        print(f"📅 Date: {date}")
        st = 12
        for _ in range(4):
            times = fetch_available_times(date, num_people, st)
            for t in times:
              tt = datetime.strptime(t, "%H:%M")
              dt_new = tt + timedelta(minutes=55)
              print(f"   ⏱ {t} ~ ", dt_new.strftime("%H:%M"))
            st += 3


if __name__ == "__main__":
    main()
