# Venue Filtering Guide

This guide shows you how to run Celery tasks for only specific venues (e.g., only `puttery_nyc` and `kick_axe_brooklyn`).

## Method 1: Using Environment Variable (Recommended for Production)

Set the `CELERY_VENUES_FILTER` environment variable with a comma-separated list of venue names.

### Windows PowerShell:
```powershell
# Set environment variable for current session
$env:CELERY_VENUES_FILTER = "puttery_nyc,kick_axe_brooklyn"

# Or set permanently (requires restart)
[System.Environment]::SetEnvironmentVariable("CELERY_VENUES_FILTER", "puttery_nyc,kick_axe_brooklyn", "User")
```

### Linux/Mac:
```bash
# Set for current session
export CELERY_VENUES_FILTER="puttery_nyc,kick_axe_brooklyn"

# Or add to ~/.bashrc or ~/.zshrc for permanent
echo 'export CELERY_VENUES_FILTER="puttery_nyc,kick_axe_brooklyn"' >> ~/.bashrc
```

### Using .env file:
Create or update `.env` file in your project root:
```
CELERY_VENUES_FILTER=puttery_nyc,kick_axe_brooklyn
```

Then load it before starting Celery:
```bash
# Linux/Mac
export $(cat .env | xargs)
celery -A celery_app worker --loglevel=info

# Or use python-dotenv
python -c "from dotenv import load_dotenv; load_dotenv()" && celery -A celery_app worker --loglevel=info
```

## Method 2: Manually Trigger with Python

You can trigger a refresh cycle with specific venues using Python:

```python
from app import refresh_all_venues_task

# Run only puttery and kick_axe
venues_filter = ['puttery_nyc', 'kick_axe_brooklyn']
result = refresh_all_venues_task.delay(venues_filter=venues_filter)
print(f"Task ID: {result.id}")
```

## Method 3: Using API Endpoint (Future Enhancement)

You could add an API endpoint to trigger filtered refresh cycles. Example:

```python
@app.route('/refresh_filtered', methods=['POST'])
def refresh_filtered():
    data = request.get_json() or {}
    venues = data.get('venues', [])
    
    if not venues:
        return jsonify({'error': 'No venues specified'}), 400
    
    result = refresh_all_venues_task.delay(venues_filter=venues)
    return jsonify({
        'message': f'Filtered refresh started for {len(venues)} venues',
        'venues': venues,
        'task_id': result.id
    })
```

## Available Venue Names

### NYC Venues:
- `swingers_nyc`
- `electric_shuffle_nyc`
- `lawn_club_nyc_indoor_gaming`
- `lawn_club_nyc_curling_lawns`
- `lawn_club_nyc_croquet_lawns`
- `spin_nyc`
- `spin_nyc_midtown`
- `five_iron_golf_nyc_fidi`
- `five_iron_golf_nyc_flatiron`
- `five_iron_golf_nyc_grand_central`
- `five_iron_golf_nyc_herald_square`
- `five_iron_golf_nyc_long_island_city`
- `five_iron_golf_nyc_upper_east_side`
- `five_iron_golf_nyc_rockefeller_center`
- `lucky_strike_nyc`
- `lucky_strike_nyc_times_square`
- `easybowl_nyc`
- `tsquaredsocial_nyc`
- `daysmart_chelsea`
- `puttery_nyc` ⭐
- `kick_axe_brooklyn` ⭐

### London Venues:
- `swingers_london`
- `electric_shuffle_london`
- `fair_game_canary_wharf`
- `fair_game_city`
- `clays_bar`
- `puttshack`
- `flight_club_darts`
- `f1_arcade`
- `topgolf_chigwell`
- `hijingo`
- `pingpong`
- `allstarlanes_stratford`
- `allstarlanes_holborn`
- `allstarlanes_white_city`
- `allstarlanes_brick_lane`

## Examples

### Example 1: Only Puttery and Kick Axe
```python
# Python
from app import refresh_all_venues_task
refresh_all_venues_task.delay(venues_filter=['puttery_nyc', 'kick_axe_brooklyn'])
```

```bash
# Environment variable
export CELERY_VENUES_FILTER="puttery_nyc,kick_axe_brooklyn"
```

### Example 2: Only NYC Venues
```python
from app import NYC_VENUES
from app import refresh_all_venues_task
refresh_all_venues_task.delay(venues_filter=NYC_VENUES)
```

### Example 3: Only London Venues
```python
from app import LONDON_VENUES
from app import refresh_all_venues_task
refresh_all_venues_task.delay(venues_filter=LONDON_VENUES)
```

### Example 4: Multiple Specific Venues
```python
venues = ['puttery_nyc', 'kick_axe_brooklyn', 'hijingo', 'pingpong']
refresh_all_venues_task.delay(venues_filter=venues)
```

## How It Works

1. When `venues_filter` is provided, the refresh cycle only creates tasks for those venues
2. The filter persists across cycles (next cycle will use the same filter)
3. Invalid venue names are logged as warnings and ignored
4. If all venues in filter are invalid, all venues are used instead (with a warning)

## Verification

Check the Celery worker logs to see which venues are being processed:

```bash
# View logs
celery -A celery_app worker --loglevel=info

# Look for lines like:
# [REFRESH] Venue filter applied: 2 venues selected: ['puttery_nyc', 'kick_axe_brooklyn']
```

## Notes

- The filter applies to all guest counts (2-8) and all dates (30 days)
- Tasks are still shuffled to interleave different guest counts and dates
- The filter is passed to the next cycle automatically, so it persists
- To remove the filter, restart Celery without the environment variable or pass `venues_filter=None`
