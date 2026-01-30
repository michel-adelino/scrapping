# How to Apply Environment Variable Changes

After setting the `CELERY_VENUES_FILTER` environment variable, you need to restart Celery services to pick up the changes.

## Method 1: Windows (PowerShell) - Running Celery Directly

If you're running Celery directly in PowerShell (not as a service):

### Step 1: Set Environment Variable
```powershell
# Set for current session
$env:CELERY_VENUES_FILTER = "puttery_nyc,kick_axe_brooklyn"

# Verify it's set
echo $env:CELERY_VENUES_FILTER
```

### Step 2: Restart Celery Services

**Stop current Celery processes:**
```powershell
# Find and stop Celery processes
Get-Process | Where-Object {$_.ProcessName -like "*celery*"} | Stop-Process -Force

# Or if running in separate terminals, just close those terminals
```

**Start Celery with the environment variable:**
```powershell
# Terminal 1: Start Celery Worker
$env:CELERY_VENUES_FILTER = "puttery_nyc,kick_axe_brooklyn"
celery -A celery_app worker --loglevel=info

# Terminal 2: Start Celery Beat
$env:CELERY_VENUES_FILTER = "puttery_nyc,kick_axe_brooklyn"
celery -A celery_app beat --loglevel=info
```

## Method 2: Windows - Using .env File

### Step 1: Create/Update .env file
Create a `.env` file in your project root:
```
CELERY_VENUES_FILTER=puttery_nyc,kick_axe_brooklyn
```

### Step 2: Load .env and Restart
```powershell
# Load environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Verify
echo $env:CELERY_VENUES_FILTER

# Restart Celery (stop old processes first)
Get-Process | Where-Object {$_.ProcessName -like "*celery*"} | Stop-Process -Force

# Start Celery Worker
celery -A celery_app worker --loglevel=info

# Start Celery Beat (in another terminal)
celery -A celery_app beat --loglevel=info
```

## Method 3: Linux/Ubuntu - Systemd Services

If you're running Celery as systemd services (production server):

### Step 1: Update Systemd Service Files

Edit the Celery Beat service file to include the environment variable:

```bash
sudo nano /etc/systemd/system/backend-scraper-celery-beat.service
```

Add the environment variable to the `[Service]` section:
```ini
[Service]
Type=simple
User=your_user
Group=your_user
WorkingDirectory=/opt/scrapping
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/scrapping/venv/bin"
Environment="CELERY_VENUES_FILTER=puttery_nyc,kick_axe_brooklyn"
ExecStart=/opt/scrapping/venv/bin/python3 -m celery -A celery_app beat --loglevel=info
Restart=always
RestartSec=10
```

### Step 2: Reload and Restart Services

```bash
# Reload systemd to pick up service file changes
sudo systemctl daemon-reload

# Restart Celery Beat (this is the one that reads the env var on startup)
sudo systemctl restart backend-scraper-celery-beat

# Optionally restart worker too (if you want fresh start)
sudo systemctl restart backend-scraper-celery-worker

# Check status
sudo systemctl status backend-scraper-celery-beat
```

### Step 3: Verify It's Working

```bash
# Check logs to see if filter is applied
sudo journalctl -u backend-scraper-celery-beat -n 50 | grep -i "filter\|venue"

# You should see:
# [Beat Startup] Venue filter from environment: ['puttery_nyc', 'kick_axe_brooklyn']
# [Beat Startup] Filtered to venues: ['puttery_nyc', 'kick_axe_brooklyn']
```

## Method 4: Linux - Using .env File with Systemd

### Step 1: Create .env file
```bash
cd /opt/scrapping  # or your project directory
nano .env
```

Add:
```
CELERY_VENUES_FILTER=puttery_nyc,kick_axe_brooklyn
```

### Step 2: Update Systemd Service to Load .env

Edit the service file:
```bash
sudo nano /etc/systemd/system/backend-scraper-celery-beat.service
```

Add this to load .env file:
```ini
[Service]
Type=simple
User=your_user
Group=your_user
WorkingDirectory=/opt/scrapping
EnvironmentFile=/opt/scrapping/.env
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/scrapping/venv/bin"
ExecStart=/opt/scrapping/venv/bin/python3 -m celery -A celery_app beat --loglevel=info
Restart=always
RestartSec=10
```

### Step 3: Reload and Restart
```bash
sudo systemctl daemon-reload
sudo systemctl restart backend-scraper-celery-beat
```

## Quick Reference: Restart Commands

### Windows (PowerShell)
```powershell
# Stop all Celery processes
Get-Process | Where-Object {$_.ProcessName -like "*celery*"} | Stop-Process -Force

# Start with environment variable
$env:CELERY_VENUES_FILTER = "puttery_nyc,kick_axe_brooklyn"
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

### Linux (Systemd)
```bash
# Restart Celery Beat (reads env var on startup)
sudo systemctl restart backend-scraper-celery-beat

# Restart Worker (optional)
sudo systemctl restart backend-scraper-celery-worker

# Check status
sudo systemctl status backend-scraper-celery-beat
```

## Important Notes

1. **Celery Beat reads the environment variable on startup** - You only need to restart Beat, not the worker
2. **The filter persists across cycles** - Once set, each cycle will use the same filter
3. **To remove the filter** - Set `CELERY_VENUES_FILTER` to empty or remove it, then restart Beat
4. **Check logs** - Always verify in logs that the filter is being applied

## Verification

After restarting, check the logs to confirm:

```bash
# Linux
sudo journalctl -u backend-scraper-celery-beat -n 20

# Windows (if running in terminal)
# Look for output like:
# [Beat Startup] Venue filter from environment: ['puttery_nyc', 'kick_axe_brooklyn']
# [Beat Startup] Filtered to venues: ['puttery_nyc', 'kick_axe_brooklyn']
```

## Troubleshooting

### Environment variable not being read?

1. **Check if it's set:**
   ```bash
   # Linux
   echo $CELERY_VENUES_FILTER
   
   # Windows PowerShell
   echo $env:CELERY_VENUES_FILTER
   ```

2. **Verify service file has Environment line:**
   ```bash
   sudo cat /etc/systemd/system/backend-scraper-celery-beat.service | grep Environment
   ```

3. **Check logs for errors:**
   ```bash
   sudo journalctl -u backend-scraper-celery-beat -n 50
   ```

4. **Restart with explicit environment:**
   ```bash
   # Linux - run directly to test
   CELERY_VENUES_FILTER="puttery_nyc,kick_axe_brooklyn" celery -A celery_app beat --loglevel=info
   ```
   
