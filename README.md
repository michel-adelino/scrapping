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

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

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

**Note:** Celery Beat schedules periodic tasks (runs scraping every 30 minutes).

### 5. Start React Frontend (Port 3000)

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

## Quick Start (All Commands)

Open **5 separate terminal windows**:

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Flask Backend:**
```bash
python app.py
```

**Terminal 3 - Celery Worker:**
```bash
# Windows
python -m celery -A celery_app worker --pool=threads --concurrency=5 --loglevel=info

# Linux/macOS
python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info
```

**Terminal 4 - Celery Beat:**
```bash
python -m celery -A celery_app beat --loglevel=info
```

**Terminal 5 - React Frontend:**
```bash
cd frontend
npm run dev
```

**Note:** The worker uses parallel processing (5 threads on Windows, 4 processes on Linux/macOS) so you only need one worker terminal.

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

### Redis Connection Error
- Make sure Redis is running: `redis-server`
- Check Redis is accessible: `redis-cli ping` (should return "PONG")

### Celery Worker Not Starting
- On Windows, make sure to use `--pool=solo`
- Check Redis is running and accessible

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
# Delete all corrupted schedule files
rm -f celerybeat-schedule*

# Then restart Celery Beat
python -m celery -A celery_app beat --loglevel=info
```

Celery Beat will automatically create new, properly formatted schedule files on startup.

