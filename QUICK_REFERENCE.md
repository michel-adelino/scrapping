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
cd /opt/backend-scraper

# Connect to SQLite database
sqlite3 availability.db
```

### Quick Database Checks (from command line)
```bash
# Count total slots
sqlite3 /opt/backend-scraper/availability.db "SELECT COUNT(*) FROM availability_slots;"

# Count by city
sqlite3 /opt/backend-scraper/availability.db "SELECT city, COUNT(*) FROM availability_slots GROUP BY city;"

# View latest 10 slots
sqlite3 /opt/backend-scraper/availability.db "SELECT venue_name, city, date, time, status FROM availability_slots ORDER BY last_updated DESC LIMIT 10;"

# Count by venue
sqlite3 /opt/backend-scraper/availability.db "SELECT venue_name, COUNT(*) FROM availability_slots GROUP BY venue_name ORDER BY COUNT(*) DESC LIMIT 20;"
```

### Useful SQL Queries (inside sqlite3)
```sql
-- Count all slots
SELECT COUNT(*) FROM availability_slots;

-- View slots by city
SELECT city, COUNT(*) FROM availability_slots GROUP BY city;

-- View recent slots
SELECT venue_name, city, date, time, status FROM availability_slots ORDER BY last_updated DESC LIMIT 20;

-- View available slots
SELECT venue_name, date, time, price FROM availability_slots WHERE UPPER(status) LIKE '%AVAILABLE%' ORDER BY date, time LIMIT 50;

-- View slots by venue
SELECT venue_name, COUNT(*) as slot_count FROM availability_slots GROUP BY venue_name ORDER BY slot_count DESC;

-- View scraping tasks
SELECT task_id, website, status, guests, target_date, created_at FROM scraping_tasks ORDER BY created_at DESC LIMIT 20;
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

