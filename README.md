# Backend - Playwright-based Scraper

This is the Playwright-based backend for the availability scraper, migrated from the Selenium-based implementation in the `scrapping` folder.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
python -m playwright install chromium
```

Note: On Windows/PowerShell, use `python -m playwright install` instead of just `playwright install`.

3. Set up environment variables (create a `.env` file):
```
DATABASE_URL=sqlite:///availability.db
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
FLASK_DEBUG=True
PORT=8010
HOST=0.0.0.0
```

4. Initialize the database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Running

**Important:** Run all commands from the `backend` directory.

1. Start Redis (required for Celery):
```bash
# On Linux/Mac:
redis-server

# On Windows, you may need to start Redis service or use WSL
# Or install Redis for Windows and start it manually
```

2. Start Celery worker (in a separate terminal):
```bash
cd backend
python -m celery -A celery_app worker --loglevel=info
```

Note: On Windows/PowerShell, use `python -m celery` instead of just `celery`.

3. Start Celery Beat (for periodic tasks, in another separate terminal):
```bash
cd backend
python -m celery -A celery_app beat --loglevel=info
```

Note: On Windows/PowerShell, use `python -m celery` instead of just `celery`.

4. Start Flask app (in another terminal):
```bash
cd backend
python app.py
```

Or use Flask CLI:
```bash
cd backend
set FLASK_APP=app.py  # On Windows
# export FLASK_APP=app.py  # On Linux/Mac
flask run --host=0.0.0.0 --port=8010
```

## Structure

- `app.py` - Main Flask application with API routes
- `celery_app.py` - Celery configuration
- `models.py` - Database models (AvailabilitySlot, ScrapingTask)
- `browser_utils.py` - Playwright browser management utilities
- `scrapers/` - Scraper implementations
  - `base_scraper.py` - Base scraper class
  - `swingers.py` - Swingers scraper (NYC and London)
  - `electric_shuffle.py` - Electric Shuffle scraper
  - Other venue scrapers (to be fully implemented)

## API Endpoints

Same as the original scrapping backend:
- `GET /api/health` - Health check
- `GET /api/data` - Get scraped availability data
- `POST /run_scraper` - Start scraping task
- `GET /task_status/<task_id>` - Get task status
- `POST /api/clear_data` - Clear data
- `POST /refresh_data` - Refresh data
- `GET /api/scraping_durations` - Get scraping durations

## Notes

- The frontend in `scrapping/frontend` should work without changes as the API endpoints match
- Some scrapers are placeholder implementations and need to be fully migrated from Selenium to Playwright
- The database can be shared with the original scrapping backend or use a separate database (configure via DATABASE_URL)

