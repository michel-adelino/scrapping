# Environment Variables Reference

This document describes all environment variables used by the Scrapping application.

## Required Variables

### Redis Configuration
- **`REDIS_URL`** (Required)
  - Default: `redis://localhost:6379/0`
  - Description: Redis connection URL for Celery task queue
  - Example: `redis://localhost:6379/0`
  - Used by: `celery_app.py`

## Optional Variables

### Flask Configuration
- **`FLASK_APP`**
  - Default: `app.py`
  - Description: Flask application entry point
  - Used by: Flask CLI

- **`FLASK_ENV`**
  - Default: `production`
  - Options: `development`, `production`
  - Description: Flask environment mode

- **`FLASK_HOST`**
  - Default: `0.0.0.0`
  - Description: Host to bind Flask server to
  - Used by: `app.py` (line 4695)

- **`FLASK_PORT`**
  - Default: `8010`
  - Description: Port to bind Flask server to
  - Used by: `app.py` (line 4696)

- **`FLASK_DEBUG`**
  - Default: `False`
  - Options: `True`, `False`, `1`, `0`, `yes`, `no`
  - Description: Enable Flask debug mode
  - Used by: `app.py` (line 4698)

### Database Configuration
- **`DATABASE_URL`** (Optional)
  - Default: `sqlite:///{project_dir}/availability.db`
  - Description: Database connection URL
  - Formats:
    - SQLite: `sqlite:////opt/scrapping/availability.db`
    - PostgreSQL: `postgresql://user:pass@host:5432/dbname`
    - MySQL: `mysql://user:pass@host:3306/dbname`
  - Used by: `app.py` (line 326)
  - Note: If not set, defaults to SQLite in project directory

### Chrome/Chromium Configuration
- **`CHROME_BINARY`** (Optional)
  - Description: Path to Chrome/Chromium binary
  - Common paths:
    - `/usr/bin/google-chrome` (Ubuntu/Debian)
    - `/usr/bin/chromium-browser` (Ubuntu/Debian)
    - `/usr/bin/chromium` (Arch Linux)
  - Used by: `app.py` (line 65)
  - Note: Application auto-detects if not set

- **`GOOGLE_CHROME_BIN`** (Optional, Alternative)
  - Description: Alternative environment variable name for Chrome binary
  - Used by: `app.py` (line 65)
  - Note: `CHROME_BINARY` takes precedence

### Frontend Configuration
- **`VITE_API_BASE`** (Optional)
  - Description: API base URL for production frontend builds
  - Example: `http://154.12.229.127:8010/api`
  - Used by: `frontend/src/App.jsx` (line 11)
  - Note: Only needed for production builds. In development, auto-detects from hostname

## Example .env File

```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=8010
FLASK_DEBUG=False

# Database (SQLite - default)
# DATABASE_URL=sqlite:////opt/scrapping/availability.db

# Redis (Required)
REDIS_URL=redis://localhost:6379/0

# Chrome Binary
CHROME_BINARY=/usr/bin/google-chrome

# Frontend API Base (for production builds)
# VITE_API_BASE=http://your-server-ip:8010/api
```

## Loading Environment Variables

The application uses `python-dotenv` to load variables from `.env` file. Make sure to:

1. Install python-dotenv:
   ```bash
   pip install python-dotenv
   ```

2. Add to your code (if not already present):
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

3. Create `.env` file in the project root directory

## Systemd Service Environment

When running as a systemd service, you can also set environment variables in the service file:

```ini
[Service]
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="CHROME_BINARY=/usr/bin/google-chrome"
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/scrapping/venv/bin"
```

## Notes

- Variables are loaded in this order:
  1. System environment variables
  2. `.env` file (via python-dotenv)
  3. Default values in code

- For production, never commit `.env` file to version control
- Use `.env.example` as a template for other developers

