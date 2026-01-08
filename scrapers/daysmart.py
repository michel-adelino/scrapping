"""
DaySmart Chelsea – API scraper (FINAL)
✔ Dynamic league per date
✔ Team-level pricing (UI accurate)
✔ Pagination safe
✔ No UI scraping
"""

import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://apps.daysmartrecreation.com/dash/jsonapi/api/v1"

HEADERS = {
    "Accept": "application/vnd.api+json",
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
}

# -------------------------------------------------
# CACHE
# -------------------------------------------------
PRODUCT_PRICE_CACHE = {}


# -------------------------------------------------
# PRODUCT PRICE (TEAM LEVEL – SOURCE OF TRUTH)
# -------------------------------------------------
def get_product_price(product_id):
    if not product_id:
        return None

    if product_id in PRODUCT_PRICE_CACHE:
        return PRODUCT_PRICE_CACHE[product_id]

    r = requests.get(
        f"{BASE_URL}/products/{product_id}",
        headers=HEADERS,
        params={"company": "chelsea"},
        timeout=15
    )
    r.raise_for_status()

    attrs = r.json().get("data", {}).get("attributes", {}) or {}

    price = (
        attrs.get("local_price")
        or attrs.get("actual_price")
        or attrs.get("price")
        or attrs.get("non_resident_price")
    )

    formatted = f"${float(price):.2f}" if price is not None else None
    PRODUCT_PRICE_CACHE[product_id] = formatted
    return formatted


# -------------------------------------------------
# LEAGUE IDS FOR DATE
# -------------------------------------------------
def get_league_ids_for_date(target_date):
    league_ids = []

    params = {
        "company": "chelsea",
        "filter[program_id]": 37,
        "filter[visible_online]": "true",
        "sort": "start_date",
        "page[size]": 10,
        "page[number]": 1,
    }

    while True:
        r = requests.get(
            f"{BASE_URL}/leagues",
            headers=HEADERS,
            params=params,
            timeout=20
        )
        r.raise_for_status()
        payload = r.json()

        for league in payload.get("data", []):
            attrs = league.get("attributes", {})
            start_date = attrs.get("start_date")

            if start_date and start_date.startswith(target_date):
                league_ids.append(league.get("id"))

        meta = payload.get("meta", {}).get("page", {})
        if meta.get("current-page") >= meta.get("last-page"):
            break

        params["page[number]"] += 1

    return league_ids


# -------------------------------------------------
# SLOTS (TEAMS)
# -------------------------------------------------
def get_slots_for_league(league_id, target_date):
    results = []

    # Calculate end date for filter (target date + 1 day at 06:00:01)
    from datetime import datetime, timedelta
    target_dt = datetime.fromisoformat(f"{target_date}T00:00:00")
    end_date_filter = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    params = {
        "cache[save]": "false",
        "page[size]": 100,
        "page[number]": 1,
        "sort": "start_date",
        "include": "allEvents,registrationInfo,facility,league.season.priorities.memberships,skillLevel,programType,sport,league.houseProduct.locations,league.individualProduct.locations,product.locations,registrableEvents",
        "filter[league_id]": league_id,
        "filter[visible_online]": "true",
        "filterRelations[registrableEvents][publish]": "true",
        "filterRelations[registrableEvents][end__gte]": end_date_filter,
        "company": "chelsea",
    }

    while True:
        r = requests.get(
            f"{BASE_URL}/teams",
            headers=HEADERS,
            params=params,
            timeout=20
        )
        r.raise_for_status()
        payload = r.json()

        # Build a map of team_id -> registration_info for availability checking
        registration_info_map = {}
        for included in payload.get("included", []):
            if included.get("type") == "team-registration-infos":
                team_id = included.get("id")
                attrs = included.get("attributes", {})
                registration_info_map[team_id] = {
                    "max_registered": attrs.get("max_registered_customers", 0),
                    "registered": attrs.get("registered_customers", 0),
                    "registration_status": attrs.get("registration_status", "closed"),
                }

        for team in payload.get("data", []):
            attrs = team.get("attributes", {})
            start_dt = attrs.get("start_date")

            if not start_dt or not start_dt.startswith(target_date):
                continue

            # Check availability from registration info
            team_id = team.get("id")
            reg_info = registration_info_map.get(team_id, {})
            max_registered = reg_info.get("max_registered", 0)
            registered = reg_info.get("registered", 0)
            reg_status = reg_info.get("registration_status", "closed")
            
            # Determine if slot is available
            is_available = (
                attrs.get("is_registration_open", False) and
                reg_status == "open" and
                registered < max_registered
            )

            # 🔑 TEAM LEVEL PRODUCT (REAL PRICE SOURCE)
            product_id = attrs.get("product_id")
            price = get_product_price(product_id)

            results.append({
                "date": target_date,
                "time": datetime.fromisoformat(start_dt).strftime("%I:%M %p"),
                "start_datetime": start_dt,
                "duration": f"{attrs.get('event_length')} minutes",
                "price": price,
                "guests": 2,
                "status": "Available" if is_available else "Closed",
                "title": attrs.get("name"),
                "league_id": league_id,
                "team_id": team_id,
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
                "website": "Chelsea Piers Golf",
            })

        meta = payload.get("meta", {}).get("page", {})
        if meta.get("current-page", 1) >= meta.get("last-page", 1):
            break

        params["page[number]"] += 1

    return results


# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
def scrape_daysmart_chelsea(target_date):
    """
    Entry used by test_scrapers.py
    """
    all_results = []

    league_ids = get_league_ids_for_date(target_date)

    if not league_ids:
        logger.warning(f"No leagues found for {target_date}")
        return []

    for league_id in league_ids:
        all_results.extend(
            get_slots_for_league(league_id, target_date)
        )

    return all_results
