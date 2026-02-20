# Guide: Adding a New Venue

This guide walks you through adding a new venue to the scraping system. We'll use **Poolhouse (Liverpool Street, London)** as an example.

## Overview

Adding a new venue requires updates in 8 main steps:
1. **Venue List** - Add to city venue list in `app.py`
2. **Booking URL** - Add booking URL mapping in `app.py`
3. **Scraper Module** - Create scraper function in `scrapers/` directory
4. **Import Scraper** - Import the scraper module in `app.py`
5. **Celery Task** - Create task wrapper in `app.py`
6. **Venue Mapping** - Add venue name mapping in `scrape_venue_task` function
7. **Task Routing** - Add routing logic in `scrape_venue_task` function
8. **Frontend Metadata** - Add venue metadata for display in `frontend/src/data/venueMetadata.js`

---

## Step-by-Step Instructions

### Step 1: Add Venue to City List

**File:** `app.py`

Add the venue identifier to the appropriate city list. For Poolhouse London:

```python
LONDON_VENUES = [
    'swingers_london',
    'electric_shuffle_london',
    'fair_game_canary_wharf',
    'fair_game_city',
    'clays_bar',
    'puttshack',
    'flight_club_darts',
    'f1_arcade',
    'topgolf_chigwell',
    'hijingo',
    'pingpong',
    'allstarlanes_stratford',
    'allstarlanes_holborn',
    'allstarlanes_white_city',
    'allstarlanes_brick_lane',
    'poolhouse_london'  # ← Add this line
]
```

**Naming Convention:**
- Use lowercase with underscores
- Format: `venue_name_city` or `venue_name_location`
- Examples: `swingers_london`, `puttery_nyc`, `kick_axe_brooklyn`

---

### Step 2: Add Booking URL

**File:** `app.py`

Add the venue's booking URL to the `VENUE_BOOKING_URLS` dictionary:

```python
VENUE_BOOKING_URLS = {
    # ... existing venues ...
    'Poolhouse (Liverpool Street)': 'https://pool.house/',  # ← Add this line
}
```

**Notes:**
- Key format: `'Venue Name (Location)'` - matches the display name
- Value: Full booking URL
- This URL is used to generate booking links in the frontend

---

### Step 3: Create Scraper Module

**File:** `scrapers/poolhouse.py`

Create a new scraper file following the base scraper pattern:

```python
"""
Poolhouse scraper (London) using Playwright
"""
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup  # Optional: for HTML parsing
import logging

logger = logging.getLogger(__name__)

def scrape_poolhouse(guests, target_date):
    """
    Scrape Poolhouse availability
    
    Args:
        guests: Number of guests (int)
        target_date: Target date in 'YYYY-MM-DD' format (str)
    
    Returns:
        List of dictionaries with availability data:
        [
            {
                'date': '2026-03-15',
                'time': '19:00',
                'price': '£50',
                'status': 'Available',
                'venue_name': 'Poolhouse (Liverpool Street)',
                'city': 'London',
                'booking_url': 'https://pool.house/'
            },
            ...
        ]
    """
    results = []
    
    try:
        # Parse target date
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        date_str = target_date
        
        # Example URL construction (adjust based on actual booking system)
        url = f"https://pool.house/book"  # Adjust based on actual booking page
        
        with BaseScraper() as scraper:
            # Navigate to booking page
            scraper.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Wait for page elements to load
            # Adjust selectors based on actual website structure
            try:
                scraper.wait_for_selector("input[type='date']", timeout=10000)
            except:
                logger.warning("Date selector not found")
            
            # Fill in date
            scraper.fill("input[type='date']", date_str)
            
            # Fill in number of guests
            scraper.fill("input[name='guests']", str(guests))
            
            # Submit or wait for results
            scraper.click("button[type='submit']")
            
            # Wait for results
            scraper.wait_for_timeout(3000)
            
            # Parse available slots
            # Option 1: Use BeautifulSoup (recommended for complex parsing)
            content = scraper.get_content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            slots = soup.find_all("div", class_="time-slot")  # Adjust selector
            
            for slot in slots:
                time_el = slot.find("span", class_="time")
                price_el = slot.find("span", class_="price")
                
                time = time_el.get_text(strip=True) if time_el else "None"
                price = price_el.get_text(strip=True) if price_el else "None"
            
            # Option 2: Use Playwright locators (for simpler cases)
            # slots = scraper.locator(".time-slot").all()
            # for slot in slots:
            #     time = slot.locator(".time").inner_text()
            #     price = slot.locator(".price").inner_text()
                
                results.append({
                    'date': date_str,
                    'time': time,
                    'price': price,
                    'status': 'Available',
                    'venue_name': 'Poolhouse (Liverpool Street)',
                    'city': 'London',
                    'booking_url': 'https://pool.house/'
                })
        
        logger.info(f"[POOLHOUSE] Found {len(results)} slots for {date_str}")
        
    except Exception as e:
        logger.error(f"[POOLHOUSE] Error scraping: {e}", exc_info=True)
    
    return results
```

**Important Notes:**
- Use `BaseScraper` context manager for browser management
- Return a list of dictionaries with required fields
- Handle errors gracefully and log them
- Adjust selectors and logic based on the actual booking website structure
- Test the scraper independently before integrating
- The scraper function signature must be: `def scrape_poolhouse(guests, target_date):`

**Required Return Format:**
Each result dictionary must include:
- `date`: Date string in 'YYYY-MM-DD' format
- `time`: Time string (e.g., '19:00' or '7:00 PM')
- `price`: Price string (e.g., '£50' or '$50')
- `status`: Status string (usually 'Available')
- `venue_name`: (Optional) Display name matching `VENUE_BOOKING_URLS` key. If not provided, the venue_name from `run_scraper_and_save_to_db` will be used.
- `city`: (Optional) 'London' or 'NYC'. If not provided, the city parameter from `run_scraper_and_save_to_db` will be used.
- `booking_url`: (Optional) Direct booking URL for this slot

---

### Step 4: Import Scraper in app.py

**File:** `app.py`

Add the import statement with other scraper imports (around line 516-517):

```python
# Import scrapers
from scrapers import swingers, electric_shuffle, lawn_club, spin, five_iron_golf, lucky_strike, easybowl
from scrapers import fair_game, clays_bar, puttshack, flight_club_darts, f1_arcade, topgolfchigwell, tsquaredsocial, daysmart, hijingo, pingpong, puttery, kick_axe, allstarlanes_bowling, poolhouse  # ← Add poolhouse
```

**Note:** The import uses the module name (e.g., `poolhouse`), not the function name. The actual scraper function `scrape_poolhouse` will be accessed as `poolhouse.scrape_poolhouse` in the task wrapper.

---

### Step 5: Create Celery Task Wrapper

**File:** `app.py`

Add a Celery task wrapper function (around line 2020, after other task functions like `scrape_kick_axe_task`):

```python
@celery_app.task(bind=True, name='app.scrape_poolhouse_task')
def scrape_poolhouse_task(self, guests, target_date, task_id=None):
    """Poolhouse (Liverpool Street) scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Poolhouse (Liverpool Street)...', current_venue='Poolhouse (Liverpool Street)')
            
            slots_saved = run_scraper_and_save_to_db(
                poolhouse.scrape_poolhouse,
                'Poolhouse (Liverpool Street)',
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
```

---

### Step 6: Add Venue Name Mapping

**File:** `app.py`

Add the venue to the `venue_name_map` dictionary in the `scrape_venue_task` function (around line 2053):

```python
venue_name_map = {
    'swingers_nyc': 'Swingers (Nomad)',
    # ... existing mappings ...
    'poolhouse_london': 'Poolhouse (Liverpool Street)',  # ← Add this line
}
```

---

### Step 7: Add Task Routing Logic

**File:** `app.py`

Add routing logic in the `scrape_venue_task` function (around line 2230, before the `else` clause):

```python
elif website == 'poolhouse_london':
    if not target_date:
        raise ValueError("Poolhouse requires a specific target date")
    result = scrape_poolhouse_task(guests, target_date, task_id)
```

**Placement:** Add this before the final `else:` clause that handles unknown websites.

---

### Step 8: Add Frontend Metadata

**File:** `frontend/src/data/venueMetadata.js`

Add venue metadata to the appropriate city section:

```javascript
// London venues metadata
const londonVenues = {
  // ... existing venues ...
  'Poolhouse (Liverpool Street)': {
    venueName: 'Poolhouse',
    location: 'Liverpool Street',
    neighborhood: 'The City',
    description: 'Pool culture reimagined for a new era. Technology-enabled pool tables with elevated food and drink.',
    city: 'London'
  }
};
```

**Fields:**
- `venueName`: Base venue name (without location)
- `location`: Specific location/neighborhood
- `neighborhood`: Area/neighborhood (can be `null`)
- `description`: Brief description of the venue
- `city`: 'London' or 'NYC'

---

## Testing Your New Venue

### 1. Test Scraper Independently

Create a test script to verify the scraper works:

```python
# test_poolhouse.py
from scrapers.poolhouse import scrape_poolhouse

# Test with 4 guests for a future date
results = scrape_poolhouse(guests=4, target_date='2026-03-15')
print(f"Found {len(results)} slots")
for slot in results:
    print(slot)
```

Run it:
```bash
python test_poolhouse.py
```

### 2. Test via API

Start the Flask app and Celery worker, then test via the API:

```bash
# Terminal 1: Start Flask
python app.py

# Terminal 2: Start Celery worker
celery -A celery_app worker --loglevel=info
```

Test via API endpoint:
```bash
curl -X POST http://localhost:5000/run_scraper \
  -H "Content-Type: application/json" \
  -d '{
    "website": "poolhouse_london",
    "guests": 4,
    "target_date": "2026-03-15"
  }'
```

### 3. Verify Database

Check that slots are being saved:

```python
from app import app, db
from models import AvailabilitySlot

with app.app_context():
    slots = AvailabilitySlot.query.filter_by(venue_name='Poolhouse (Liverpool Street)').all()
    print(f"Found {len(slots)} slots in database")
    for slot in slots[:5]:  # Show first 5
        print(f"{slot.date} {slot.time} - {slot.price} ({slot.status})")
```

### 4. Check Frontend Display

Start the frontend and verify the venue appears:

```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:3000` and verify:
- Venue appears in the venue list
- Metadata displays correctly
- Slots show up when filtering by venue

---

## Common Issues and Solutions

### Issue: Scraper returns empty results

**Solutions:**
- Check if selectors match the actual website structure
- Verify the website hasn't changed
- Add more wait time for dynamic content
- Check browser console for JavaScript errors
- Test with `headless=False` to see what's happening

### Issue: "Unknown website" error

**Solutions:**
- Verify venue is added to `LONDON_VENUES` or `NYC_VENUES`
- Check routing logic in `scrape_venue_task` function
- Ensure venue identifier matches exactly (case-sensitive)

### Issue: Venue not appearing in frontend

**Solutions:**
- Verify metadata is added to `venueMetadata.js`
- Check that venue name matches exactly (including parentheses and capitalization)
- Clear browser cache
- Restart frontend dev server

### Issue: Booking URL not working

**Solutions:**
- Verify URL is correct in `VENUE_BOOKING_URLS`
- Check if URL requires parameters (guests, date, etc.)
- Test URL manually in browser

---

## Example: Complete Poolhouse Implementation

Here's a complete example showing all the changes needed for Poolhouse:

### 1. app.py - Venue List (line ~147)
```python
LONDON_VENUES = [
    # ... existing venues ...
    'poolhouse_london'
]
```

### 2. app.py - Booking URL (line ~165)
```python
VENUE_BOOKING_URLS = {
    # ... existing venues ...
    'Poolhouse (Liverpool Street)': 'https://pool.house/',
}
```

### 3. scrapers/poolhouse.py - New file
```python
"""Poolhouse scraper (London)"""
from datetime import datetime
from scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

def scrape_poolhouse(guests, target_date):
    results = []
    # ... scraper implementation ...
    return results
```

### 4. app.py - Import (line ~517)
```python
from scrapers import poolhouse
```

### 5. app.py - Task wrapper (after line ~2020)
```python
@celery_app.task(bind=True, name='app.scrape_poolhouse_task')
def scrape_poolhouse_task(self, guests, target_date, task_id=None):
    """Poolhouse (Liverpool Street) scraper as Celery task"""
    with app.app_context():
        try:
            if task_id:
                update_task_status(task_id, status='STARTED', progress='Starting to scrape Poolhouse (Liverpool Street)...', current_venue='Poolhouse (Liverpool Street)')
            
            slots_saved = run_scraper_and_save_to_db(
                poolhouse.scrape_poolhouse,
                'Poolhouse (Liverpool Street)',
                'London',
                guests,
                guests,  # Note: guests appears twice - first is for DB, second is passed to scraper function via *args
                target_date,
                task_id=task_id
            )
```

**Important:** Notice that `guests` is passed twice:
- The first `guests` parameter is used by `run_scraper_and_save_to_db` for database operations
- The second `guests` (in `*args`) is passed to the scraper function `scrape_poolhouse(guests, target_date)`
- This pattern matches all existing scrapers in the codebase
            
            if task_id:
                update_task_status(task_id, status='SUCCESS', progress=f'Found {slots_saved} slots', total_slots=slots_saved)
            
            return {'status': 'success', 'slots_found': slots_saved}
        except Exception as e:
            if task_id:
                update_task_status(task_id, status='FAILURE', error=str(e))
            raise e
```

### 6. app.py - Venue mapping (line ~2053)
```python
venue_name_map = {
    # ... existing mappings ...
    'poolhouse_london': 'Poolhouse (Liverpool Street)',
}
```

### 7. app.py - Routing (line ~2230)
```python
elif website == 'poolhouse_london':
    if not target_date:
        raise ValueError("Poolhouse requires a specific target date")
    result = scrape_poolhouse_task(guests, target_date, task_id)
```

### 8. frontend/src/data/venueMetadata.js (line ~189)
```javascript
const londonVenues = {
  // ... existing venues ...
  'Poolhouse (Liverpool Street)': {
    venueName: 'Poolhouse',
    location: 'Liverpool Street',
    neighborhood: 'The City',
    description: 'Pool culture reimagined for a new era.',
    city: 'London'
  }
};
```

---

## Checklist

Use this checklist when adding a new venue:

- [ ] Added venue identifier to `LONDON_VENUES` or `NYC_VENUES` in `app.py`
- [ ] Added booking URL to `VENUE_BOOKING_URLS` in `app.py`
- [ ] Created scraper module in `scrapers/` directory
- [ ] Imported scraper in `app.py`
- [ ] Created Celery task wrapper function
- [ ] Added venue to `venue_name_map` in `scrape_venue_task`
- [ ] Added routing logic in `scrape_venue_task` function
- [ ] Added metadata to `venueMetadata.js`
- [ ] Tested scraper independently
- [ ] Tested via API endpoint
- [ ] Verified slots are saved to database
- [ ] Verified venue appears in frontend

---

## Additional Resources

- **Base Scraper Documentation:** See `scrapers/base_scraper.py` for available methods
- **Existing Scrapers:** Reference `scrapers/swingers.py` or `scrapers/electric_shuffle.py` for examples
- **Database Model:** See `models.py` for `AvailabilitySlot` structure
- **Task Management:** See `app.py` for task status tracking

---

## Notes

- **Venue Naming:** Keep venue identifiers consistent across all files
- **Error Handling:** Always wrap scraper logic in try/except blocks
- **Logging:** Use logger for debugging and monitoring
- **Testing:** Test thoroughly before deploying to production
- **Documentation:** Update this guide if you discover new patterns or requirements

---

**Last Updated:** 2026-01-XX
**Example Venue:** Poolhouse (Liverpool Street, London)
**Website:** https://pool.house/
