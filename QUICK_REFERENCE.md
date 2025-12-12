# Quick Reference - Backend Scraper Commands

## Service Management

### Reload Systemd After Modifying Service Files
```bash
# After editing service files in /etc/systemd/system/
sudo systemctl daemon-reload

# Then restart the service
sudo systemctl restart backend-scraper-celery-worker
```

### Start All Services
```bash
sudo systemctl start backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

### Stop All Services
```bash
sudo systemctl stop backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

### Restart All Services
```bash
sudo systemctl restart backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

### Check Status
```bash
sudo systemctl status backend-scraper-flask
sudo systemctl status backend-scraper-celery-worker
sudo systemctl status backend-scraper-celery-beat
```

### Enable Auto-Start on Boot
```bash
sudo systemctl enable backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

## View Logs

All systemd service logs are stored in the systemd journal. Use `journalctl` to view them.

### Real-time Logs (Follow Mode)
```bash
# Flask Backend
sudo journalctl -u backend-scraper-flask -f

# Celery Worker
sudo journalctl -u backend-scraper-celery-worker -f

# Celery Beat
sudo journalctl -u backend-scraper-celery-beat -f
```

### View Last N Lines
```bash
# Last 100 lines
sudo journalctl -u backend-scraper-flask -n 100
sudo journalctl -u backend-scraper-celery-worker -n 100

# Last 50 lines
sudo journalctl -u backend-scraper-celery-worker -n 50
```

### Logs by Time Range
```bash
# Logs since today
sudo journalctl -u backend-scraper-flask --since today

# Logs since yesterday
sudo journalctl -u backend-scraper-flask --since yesterday

# Logs since specific time
sudo journalctl -u backend-scraper-flask --since "2025-11-30 07:00:00"

# Logs between two times
sudo journalctl -u backend-scraper-flask --since "2025-11-30 07:00:00" --until "2025-11-30 08:00:00"
```

### View All Logs (No Filter)
```bash
# All logs for a service
sudo journalctl -u backend-scraper-flask

# All logs with timestamps
sudo journalctl -u backend-scraper-flask --no-pager
```

### Search Logs
```bash
# Search for specific text
sudo journalctl -u backend-scraper-celery-worker | grep "error"

# Case-insensitive search
sudo journalctl -u backend-scraper-flask | grep -i "exception"

# Search for refresh cycle logs
sudo journalctl -u backend-scraper-celery-worker | grep "REFRESH"
```

### Export Logs to File
```bash
# Export to file
sudo journalctl -u backend-scraper-flask > flask_logs.txt

# Export last 1000 lines
sudo journalctl -u backend-scraper-celery-worker -n 1000 > worker_logs.txt
```

## Update Application

```bash
cd /opt/backend-scraper

# Pull latest code (if using Git)
git pull

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# Update Playwright browsers (if needed)
python -m playwright install chromium

# Restart services
sudo systemctl restart backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

## Scraping Cycle Information

### Cycle Details
- **Total Tasks per Cycle**: 4,830 tasks
  - 23 venues (15 NYC + 8 London)
  - 7 guest counts (2, 3, 4, 5, 6, 7, 8)
  - 30 dates
  - Formula: 23 × 7 × 30 = 4,830

### How Cycles Work
1. **Beat starts**: Automatically triggers first cycle
2. **Tasks created**: 4,830 tasks created and shuffled
3. **Execution**: Tasks run in parallel (concurrency=10 by default)
4. **Auto-chaining**: When cycle completes, next cycle starts automatically
5. **Continuous**: Cycles continue until worker/beat stops

### Check Cycle Status
```bash
# View refresh cycle logs
sudo journalctl -u backend-scraper-celery-worker | grep "REFRESH"

# View task completion logs
sudo journalctl -u backend-scraper-celery-worker | grep "Current cycle completed"
```

## Troubleshooting

### Check Database Path Used by Flask Service

If the Flask service shows 0 slots but you know data exists, check which database file it's using:

```bash
# Check the systemd service file to see the working directory
sudo cat /etc/systemd/system/backend-scraper-flask.service | grep WorkingDirectory

# Check what database file Flask is actually using
sudo journalctl -u backend-scraper-flask -n 50 | grep "Database URI\|File path"

# Or check the actual database file location
ls -lh /opt/scrapping/availability.db

# Check if there are multiple database files
find /opt/scrapping -name "availability.db" -type f
```

### Check if Services are Running
```bash
sudo systemctl status backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

### Check Ports
```bash
sudo netstat -tlnp | grep -E '8010|6379'
# or
sudo ss -tlnp | grep -E '8010|6379'
```

### Test Redis
```bash
redis-cli ping
```

### Test Database
```bash
cd /opt/backend-scraper
source venv/bin/activate
python3 -c "from app import app, db; app.app_context().push(); print('OK')"
```

### Test Playwright
```bash
cd /opt/backend-scraper
source venv/bin/activate
python -m playwright --version
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

### Install Playwright Browsers (if missing)
If you get errors like "Executable doesn't exist at /home/user/.cache/ms-playwright/chromium-...", run:
```bash
cd /opt/backend-scraper  # or /opt/scrapping
source venv/bin/activate
python -m playwright install chromium
# This downloads the browser binaries (may take a few minutes)
```

### Check Chrome
```bash
google-chrome --version
which google-chrome
```

## Database Access (SQLite)

### Connect to Database
```bash
# Navigate to project directory
# On Ubuntu server:
cd /opt/scrapping

# On Windows (if in project folder):
cd C:\Users\iida\Documents\Projects\scraper\scrapping

# Connect to SQLite database
sqlite3 availability.db
```

### Quick Database Checks (from command line)
```bash
# Database location (adjust path as needed)
# On Ubuntu server: /opt/scrapping/availability.db
# On Windows: C:\Users\iida\Documents\Projects\scraper\scrapping\availability.db

# Count total slots
sqlite3 /opt/scrapping/availability.db "SELECT COUNT(*) FROM availability_slots;"

# Count by city (check what city values exist)
sqlite3 /opt/scrapping/availability.db "SELECT city, COUNT(*) FROM availability_slots GROUP BY city;"

# Check all unique cities
sqlite3 /opt/scrapping/availability.db "SELECT DISTINCT city FROM availability_slots;"

# Check all unique guest counts
sqlite3 /opt/scrapping/availability.db "SELECT DISTINCT guests FROM availability_slots ORDER BY guests;"

# View latest 10 slots
sqlite3 /opt/scrapping/availability.db "SELECT venue_name, city, date, time, guests, status FROM availability_slots ORDER BY last_updated DESC LIMIT 10;"

# Count by venue
sqlite3 /opt/scrapping/availability.db "SELECT venue_name, COUNT(*) FROM availability_slots GROUP BY venue_name ORDER BY COUNT(*) DESC LIMIT 20;"

# Check slots for NYC
sqlite3 /opt/scrapping/availability.db "SELECT COUNT(*) FROM availability_slots WHERE city = 'NYC';"

# Check slots for London
sqlite3 /opt/scrapping/availability.db "SELECT COUNT(*) FROM availability_slots WHERE city = 'London';"

# Check slots for NYC with 6 guests
sqlite3 /opt/scrapping/availability.db "SELECT COUNT(*) FROM availability_slots WHERE city = 'NYC' AND guests = 6;"

# Check which guest counts have data in the database
sqlite3 /opt/scrapping/availability.db "SELECT guests, COUNT(*) FROM availability_slots GROUP BY guests ORDER BY guests;"

# Check guest counts 7 and 8 specifically
sqlite3 /opt/scrapping/availability.db "SELECT city, guests, COUNT(*) FROM availability_slots WHERE guests IN (7, 8) GROUP BY city, guests ORDER BY city, guests;"

# Check if tasks have run for guest counts 7 and 8
sqlite3 /opt/scrapping/availability.db "SELECT guests, COUNT(*) as tasks, SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful FROM scraping_tasks WHERE guests IN (7, 8) GROUP BY guests;"
```

### Useful SQL Queries (inside sqlite3)
```sql
-- Count all slots
SELECT COUNT(*) FROM availability_slots;

-- View slots by city (check what city values are actually stored)
SELECT city, COUNT(*) FROM availability_slots GROUP BY city;

-- Check all unique city values (important for debugging API queries)
SELECT DISTINCT city FROM availability_slots;

-- Check all unique venue names
SELECT DISTINCT venue_name FROM availability_slots ORDER BY venue_name;

-- Check all unique guest counts
SELECT DISTINCT guests FROM availability_slots ORDER BY guests;

-- View recent slots
SELECT venue_name, city, date, time, guests, status FROM availability_slots ORDER BY last_updated DESC LIMIT 20;

-- View available slots
SELECT venue_name, date, time, price FROM availability_slots WHERE UPPER(status) LIKE '%AVAILABLE%' ORDER BY date, time LIMIT 50;

-- View slots by venue
SELECT venue_name, COUNT(*) as slot_count FROM availability_slots GROUP BY venue_name ORDER BY slot_count DESC;

-- Check slots for specific city (NYC)
SELECT venue_name, date, time, guests, price, status 
FROM availability_slots 
WHERE city = 'NYC' 
ORDER BY date, time 
LIMIT 20;

-- Check slots for specific city (London)
SELECT venue_name, date, time, guests, price, status 
FROM availability_slots 
WHERE city = 'London' 
ORDER BY date, time 
LIMIT 20;

-- Check slots for specific city and guests
SELECT venue_name, date, time, price, status 
FROM availability_slots 
WHERE city = 'NYC' AND guests = 6 
ORDER BY date, time 
LIMIT 20;

-- Check if city values might have different casing or spaces
SELECT city, COUNT(*) 
FROM availability_slots 
GROUP BY city 
ORDER BY city;

-- Sample data to see structure
SELECT id, venue_name, city, guests, date, time, price, status, last_updated 
FROM availability_slots 
LIMIT 5;

-- Check which guest counts have data in the database
SELECT guests, COUNT(*) as slot_count 
FROM availability_slots 
GROUP BY guests 
ORDER BY guests;

-- Check guest counts by city
SELECT city, guests, COUNT(*) as slot_count 
FROM availability_slots 
GROUP BY city, guests 
ORDER BY city, guests;

-- Check if tasks have run for specific guest counts (check scraping_tasks table)
SELECT guests, COUNT(*) as task_count, 
       SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
       SUM(CASE WHEN status = 'FAILURE' THEN 1 ELSE 0 END) as failed,
       SUM(CASE WHEN status = 'STARTED' THEN 1 ELSE 0 END) as in_progress
FROM scraping_tasks 
GROUP BY guests 
ORDER BY guests;

-- Check recent tasks for guest counts 7 and 8
SELECT task_id, website, guests, target_date, status, created_at, last_updated
FROM scraping_tasks 
WHERE guests IN (7, 8)
ORDER BY created_at DESC 
LIMIT 20;

-- Check if refresh cycle has run (look for refresh_all_venues_task)
SELECT task_id, website, guests, status, created_at, progress
FROM scraping_tasks 
WHERE website LIKE 'all_%' OR website LIKE 'refresh%'
ORDER BY created_at DESC 
LIMIT 10;

-- View scraping tasks
SELECT task_id, website, status, guests, target_date, created_at FROM scraping_tasks ORDER BY created_at DESC LIMIT 20;

-- Delete unwanted Flight Club Darts locations (keep only Angel, Bloomsbury, Shoreditch, Victoria)
-- First, check what Flight Club Darts venues exist
SELECT DISTINCT venue_name FROM availability_slots WHERE venue_name LIKE 'Flight Club Darts%';

-- Delete all Flight Club Darts records EXCEPT the 4 allowed locations
DELETE FROM availability_slots 
WHERE venue_name LIKE 'Flight Club Darts%' 
AND venue_name NOT IN (
    'Flight Club Darts (Angel)',
    'Flight Club Darts (Bloomsbury)',
    'Flight Club Darts (Shoreditch)',
    'Flight Club Darts (Victoria)'
);

-- Verify deletion (should only show the 4 allowed locations)
SELECT DISTINCT venue_name FROM availability_slots WHERE venue_name LIKE 'Flight Club Darts%';
```

## Database Backup (SQLite)

### Backup
```bash
# Simple file copy
cp /opt/backend-scraper/availability.db /opt/backend-scraper/availability_backup_$(date +%Y%m%d).db

# Or use sqlite3 backup command
sqlite3 /opt/backend-scraper/availability.db ".backup /opt/backend-scraper/availability_backup_$(date +%Y%m%d).db"
```

### Restore
```bash
cp /opt/backend-scraper/availability_backup_YYYYMMDD.db /opt/backend-scraper/availability.db
```

## Firewall

### Check Status
```bash
sudo ufw status
```

### Allow Ports
```bash
sudo ufw allow 8010/tcp
```

## File Locations

- Application: `/opt/backend-scraper`
- Logs: `sudo journalctl -u service-name`
- Environment: `/opt/backend-scraper/.env`
- Service Files: `/etc/systemd/system/backend-scraper-*.service`
- Database: `/opt/backend-scraper/availability.db`

## Manual Task Management

### Manually Trigger Refresh Cycle
```bash
cd /opt/backend-scraper
source venv/bin/activate
python3 -c "from app import refresh_all_venues_task; refresh_all_venues_task.delay()"
```

### Check Celery Task Status
```bash
cd /opt/backend-scraper
source venv/bin/activate
python3 -c "from celery_app import celery_app; from celery.result import AsyncResult; print('Celery tasks can be checked via API endpoint /task_status/<task_id>')"
```

## Adjusting Concurrency

To change the number of parallel tasks, edit the service file:
```bash
sudo nano /etc/systemd/system/backend-scraper-celery-worker.service
```

Change `--concurrency=10` to your desired value, then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart backend-scraper-celery-worker
```

## Venue Information

### Total Venues: 23
- **NYC**: 15 venues
  - Swingers NYC
  - Electric Shuffle NYC
  - Lawn Club (3 options: Indoor Gaming, Curling Lawns, Croquet Lawns)
  - SPIN NYC
  - Five Iron Golf (7 locations: FiDi, Flatiron, Grand Central, Herald Square, Long Island City, Upper East Side, Rockefeller Center)
  - Lucky Strike NYC
  - Easybowl NYC

- **London**: 8 venues
  - Swingers London
  - Electric Shuffle London
  - Fair Game (2 locations: Canary Wharf, City)
  - Clays Bar (1 entry, but can scrape multiple locations)
  - Puttshack (1 entry, but can scrape multiple locations)
  - Flight Club Darts (1 entry, scrapes all 4 locations: Bloomsbury, Angel, Shoreditch, Victoria)
  - F1 Arcade

### Scraping Operations per Cycle
- 4,830 total operations (23 venues × 7 guests × 30 dates)
- Tasks are shuffled to interleave different venues and reduce IP blocking risk

