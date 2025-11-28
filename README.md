# Availability Scraper

A web application that scrapes restaurant and venue availability data from multiple websites, stores it in a database, and displays it through a React frontend.

## Features

- Scrapes availability data from multiple NYC and London venues
- Background task processing with Celery
- Real-time data display with React frontend
- Automatic periodic scraping (every 15 minutes)
- Duration tracking for each scraping queue

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Redis server (required for Celery)

### Installing Redis

**Windows:**
- Option 1: Use WSL (Windows Subsystem for Linux) and install Redis in WSL
- Option 2: Download Redis for Windows from [here](https://github.com/microsoftarchive/redis/releases)

**macOS:**
```bash
brew install redis
```

**Linux:**
```bash
sudo apt-get install redis-server  # Ubuntu/Debian
sudo yum install redis             # CentOS/RHEL
```

## Installation

### 1. Set Up Python Virtual Environment (Recommended)

**Ubuntu/Linux (VPS):**

Modern Ubuntu systems (22.04+) use externally-managed Python environments. You must create a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Or use the automated setup script:**
```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

**Windows/macOS:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** Always activate the virtual environment before running the application. You'll see `(venv)` in your terminal prompt when it's active.

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Running the Application

You need to run **4 separate processes** for the complete application:

### 1. Start Redis Server

**Windows (WSL):**
```bash
wsl redis-server
```

**macOS/Linux:**
```bash
redis-server
```

**Ubuntu VPS (if Redis is installed as a service):**
```bash
# Check if Redis is already running
redis-cli ping
# Should return: PONG

# If Redis is not running, start it:
sudo systemctl start redis-server

# To enable Redis to start on boot:
sudo systemctl enable redis-server

# If you get "Address already in use" error, Redis is already running - you're good to go!
```

### 2. Start Flask Backend (Port 8010)

```bash
python app.py
```

The backend will start on `http://localhost:8010`

### 3. Start Celery Worker

**Windows (Single worker with threads pool for parallel processing):**

```bash
python -m celery -A celery_app worker --pool=threads --concurrency=5 --loglevel=info
```

**Linux/macOS (Single worker with prefork pool):**

```bash
python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info
```

**Note:** 
- On Windows, `threads` pool allows multiple tasks to run in parallel within a single worker (default: 5 concurrent threads)
- Adjust `--concurrency=N` based on your PC's performance (3-8 is recommended)
- On Linux/macOS, `prefork` pool uses multiple processes for parallel processing

### 4. Start Celery Beat (Scheduler)

```bash
python -m celery -A celery_app beat --loglevel=info
```

**For better debugging (if Beat seems stuck):**
```bash
python -m celery -A celery_app beat --loglevel=debug
```

**Note:** Celery Beat schedules periodic tasks (runs scraping every 30 minutes). If Beat shows "Starting..." then nothing, see troubleshooting below.

### 5. Start React Frontend (Port 3000)

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

**For VPS/External Access:**
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

This allows access from external IP addresses (e.g., `http://YOUR_VPS_IP:3000`)

## Quick Start for Ubuntu VPS

After setting up the virtual environment, you need to run **5 processes**. Here's what needs the virtual environment:

✅ **Need Virtual Environment (Python processes):**
- Flask Backend
- Celery Worker  
- Celery Beat

❌ **Don't Need Virtual Environment:**
- Redis (system service)
- React Frontend (Node.js/npm)

### Using screen or tmux (Recommended for VPS)

Since you're on a VPS, you can use `screen` or `tmux` to manage multiple sessions:

```bash
# Install screen (if not installed)
sudo apt install screen

# Create named screen sessions
screen -S redis -d -m redis-server
screen -S flask -d -m bash -c "cd $(pwd) && source venv/bin/activate && python app.py"
screen -S celery-worker -d -m bash -c "cd $(pwd) && source venv/bin/activate && python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info"
screen -S celery-beat -d -m bash -c "cd $(pwd) && source venv/bin/activate && python -m celery -A celery_app beat --loglevel=info"
screen -S frontend -d -m bash -c "cd $(pwd)/frontend && npm run dev"

# View running sessions
screen -ls

# Attach to a session (e.g., to see logs)
screen -r flask

# Detach from screen: Press Ctrl+A then D
```

## Quick Start (All Commands)

Open **5 separate terminal windows** (or use screen/tmux):

**Terminal 1 - Redis:**
```bash
# Check if Redis is already running (common on Ubuntu VPS)
redis-cli ping
# If it returns "PONG", Redis is already running - skip to Terminal 2!

# If Redis is not running, start it:
# Ubuntu/Debian (service):
sudo systemctl start redis-server
# Or manually:
redis-server
```

**Terminal 2 - Flask Backend:**
```bash
# Activate virtual environment first (REQUIRED for Python processes)
source venv/bin/activate
python app.py
```

**Terminal 3 - Celery Worker:**
```bash
# Activate virtual environment first (REQUIRED for Python processes)
source venv/bin/activate
# Linux/macOS
python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info
```

**Terminal 4 - Celery Beat:**
```bash
# Activate virtual environment first (REQUIRED for Python processes)
source venv/bin/activate
python -m celery -A celery_app beat --loglevel=info
```

**Terminal 5 - React Frontend:**
```bash
# NO virtual environment needed (this is Node.js, not Python)
cd frontend
# For localhost only:
npm run dev
# For VPS/external access:
npm run dev -- --host 0.0.0.0
```

**Important Notes:**
- **Python processes** (Flask, Celery Worker, Celery Beat) **MUST** have the virtual environment activated
- **Redis** and **npm** processes do **NOT** need the virtual environment
- The worker uses parallel processing (5 threads on Windows, 4 processes on Linux/macOS) so you only need one worker terminal
- On Ubuntu VPS, you can use `screen` or `tmux` to manage multiple terminal sessions

## Application Structure

```
availability-scraper/
├── app.py                 # Flask backend application
├── celery_app.py         # Celery configuration
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── frontend/             # React frontend
│   ├── src/
│   │   ├── App.jsx       # Main React component
│   │   └── components/   # React components
│   ├── package.json      # Node.js dependencies
│   └── vite.config.js    # Vite configuration
└── README.md             # This file
```

## Usage

1. **Access the frontend:** Open `http://localhost:3000` in your browser
2. **Search for availability:** Use the search panel to filter by venue, date, and number of guests
3. **View results:** Available slots are displayed in a table or card layout
4. **Book slots:** Click "Book Now" buttons to open booking pages in new tabs

## Background Scraping

The application automatically scrapes data every 15 minutes for:
- NYC venues (30 days from today)
- London venues (30 days from today)
- Default guest count: 6 guests

Scraping durations are tracked and displayed in the Status section.

## API Endpoints

- `GET /api/data` - Get availability data (supports filters: venue_name, city, date_from, date_to, guests)
- `POST /api/clear_data` - Clear all data from database
- `GET /api/scraping_durations` - Get scraping duration statistics
- `GET /api/health` - Health check endpoint

## Troubleshooting

### Externally-Managed-Environment Error (Ubuntu/Linux)

If you see an error like:
```
error: externally-managed-environment
× This environment is externally managed
```

**Solution:** Create and use a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Now install dependencies
pip install -r requirements.txt
```

**Important:** Always activate the virtual environment (`source venv/bin/activate`) before running any Python commands. The virtual environment must be activated in each terminal window where you run the application.

### Redis Connection Error

**If Redis is already running (common on Ubuntu VPS):**
```bash
# Check if Redis is accessible
redis-cli ping
# Should return: PONG
```

**If Redis is not running:**
```bash
# Ubuntu/Debian (if installed as service):
sudo systemctl start redis-server

# Or run manually:
redis-server
```

**If you see "Address already in use" error:**
- Redis is already running - you don't need to start it again!
- Just verify it's working: `redis-cli ping` (should return "PONG")

### Celery Worker Not Starting
- On Windows, make sure to use `--pool=threads` (not `solo`)
- Check Redis is running and accessible
- See `TROUBLESHOOTING_CELERY.md` for detailed debugging steps

### Frontend Not Connecting to Backend
- Verify Flask is running on port 8010
- Check browser console for CORS errors
- Ensure frontend is configured to call `http://localhost:8010/api`

### Database Errors
- The database (`availability.db`) is created automatically on first run
- If you see database errors, try deleting `availability.db` and restarting

## Development

### Backend Development
- Flask runs in debug mode by default
- Changes to Python files require restarting Flask

### Frontend Development
- Vite provides hot module replacement
- Changes to React files are automatically reflected

## Notes

- The database file (`availability.db`) is automatically created
- Celery Beat schedule file (`celerybeat-schedule.dat`) is automatically created (or will be created on first run)
- These files are excluded from version control (see `.gitignore`)

## Troubleshooting Celery Beat

### Error: `FileNotFoundError` or `EOFError: Ran out of input`

If you see errors about `celerybeat-schedule.dat`, the schedule file is corrupted or missing. Fix it by:

**Windows PowerShell:**
```powershell
# Delete all corrupted schedule files
Remove-Item -Force -Recurse -ErrorAction SilentlyContinue "celerybeat-schedule*"

# Then restart Celery Beat - it will create fresh files
python -m celery -A celery_app beat --loglevel=info
```

**Linux/macOS:**
```bash
# Stop Celery Beat first (Ctrl+C if running)
# Delete all corrupted schedule files
rm -f celerybeat-schedule*

# If you get "Resource temporarily unavailable" error, the file might be locked:
# Wait a few seconds, or kill any running beat processes:
pkill -f "celery.*beat"

# Then delete the files and restart
rm -f celerybeat-schedule*
python -m celery -A celery_app beat --loglevel=info
```

Celery Beat will automatically create new, properly formatted schedule files on startup.

**Note:** If you see the error but Beat still shows "Current schedule:" with your tasks listed, Beat is actually working! The error is just about cleaning up old files.

### Celery Beat Shows "Starting..." Then Nothing

If Celery Beat starts but doesn't show any schedule information:

1. **Check if tasks are registered:**
   ```bash
   source venv/bin/activate
   python test_celery.py
   ```

2. **Make sure Flask app is imported:**
   - The tasks are in `app.py`, so Beat needs to import it
   - The `celery_app.py` should have `include=['app']` (already configured)

3. **Try running Beat with debug logging:**
   ```bash
   source venv/bin/activate
   python -m celery -A celery_app beat --loglevel=debug
   ```
   You should see messages about discovered tasks and the beat schedule.

4. **Check if the task name matches:**
   - Beat schedule uses: `'app.refresh_all_venues_task'`
   - Task is registered as: `@celery_app.task(name='app.refresh_all_venues_task')`
   - These must match exactly!

5. **Verify Redis connection:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### Celery Worker Shows "ready" But No Tasks Processing

If the worker is ready but not processing tasks:

1. **Check if tasks are being sent:**
   - Look at Beat logs - it should show when tasks are scheduled
   - Check Flask logs if you trigger tasks manually

2. **Verify worker can see tasks:**
   ```bash
   source venv/bin/activate
   python -m celery -A celery_app inspect registered
   ```
   This should list all registered tasks.

3. **Test a task manually:**
   ```bash
   source venv/bin/activate
   python -c "from celery_app import celery_app; from app import refresh_all_venues_task; result = refresh_all_venues_task.delay(); print(f'Task ID: {result.id}')"
   ```
   Then check worker logs to see if it processes the task.

