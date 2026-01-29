# Update Guide - Making Changes to Your Application

## Table of Contents

1. [Overview](#overview)
2. [Before You Start](#before-you-start)
3. [Method 1: Updating via Git](#method-1-updating-via-git)
4. [Method 2: Updating via File Upload](#method-2-updating-via-file-upload)
5. [Updating the Frontend](#updating-the-frontend)
6. [After Updating](#after-updating)
7. [Troubleshooting Updates](#troubleshooting-updates)

---

## Overview

This guide explains how to update your application when new versions or fixes are available. There are two methods:

- **Method 1: Git** - Recommended if you have Git access to the code repository
- **Method 2: File Upload** - Use if you receive updated files via email, download, or file transfer

Both methods will update your application and restart the services automatically.

---

## Before You Start

### Important: Backup First!

Before making any updates, create a backup of your database:

```bash
cd /opt/scrapping
cp availability.db availability_backup_$(date +%Y%m%d_%H%M%S).db
```

**Why**: If something goes wrong during the update, you can restore your data.

### Check Current Status

Verify all services are running before updating:

```bash
sudo systemctl status backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

All should show "active (running)". If any are stopped or failed, fix those issues first before updating.

---

## Method 1: Updating via Git

This method is used when the code is stored in a Git repository (like GitHub, GitLab, etc.).

### Step 1: Connect to Your Server

SSH into your server:
```bash
ssh username@your-server-ip
```

### Step 2: Navigate to Application Directory

```bash
cd /opt/scrapping
```

### Step 3: Check Current Status

See what changes will be pulled:
```bash
git fetch
git status
```

This shows if there are updates available and what files will change.

### Step 4: Pull Latest Code

Download the latest code:
```bash
git pull
```

**What this does**: Downloads the newest version of all files from the repository.

**If you see errors**:
- "Your local changes would be overwritten": You have local changes. See [Troubleshooting](#troubleshooting-updates) section.
- "Authentication failed": You may need to set up Git credentials or use SSH keys.

### Step 5: Update Python Dependencies

New code might require updated Python packages:

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**What this does**: Installs any new or updated Python packages needed by the application.

### Step 6: Update Playwright Browsers (if needed)

If the update includes browser-related changes:

```bash
source venv/bin/activate
python -m playwright install chromium
```

**Note**: This only needs to be run if you're told browser updates are required.

### Step 7: Run the Update Script

The project includes an automated update script that handles service restarts:

```bash
bash update_server.sh
```

**What this script does**:
- Updates Python dependencies
- Updates Playwright browsers
- Updates systemd service files
- Reloads systemd configuration
- Restarts all services

**Alternative**: If the script doesn't work, manually restart services:
```bash
sudo systemctl daemon-reload
sudo systemctl restart backend-scraper-flask
sudo systemctl restart backend-scraper-celery-worker
sudo systemctl restart backend-scraper-celery-beat
```

### Step 8: Verify Update

Check that services restarted successfully:

```bash
sudo systemctl status backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

All should show "active (running)".

### Step 9: Check Logs

View recent logs to ensure everything is working:

```bash
sudo journalctl -u backend-scraper-flask -n 20
sudo journalctl -u backend-scraper-celery-worker -n 20
```

Look for any error messages in red.

---

## Method 2: Updating via File Upload

This method is used when you receive updated files via email, download, FTP, or file transfer.

### Step 1: Prepare Updated Files

Make sure you have all the updated files ready. Typically you'll receive:
- Updated Python files (`.py` files)
- Updated `requirements.txt` (if dependencies changed)
- Updated frontend files (if frontend changed)
- Any new files

### Step 2: Connect to Your Server

SSH into your server:
```bash
ssh username@your-server-ip
```

### Step 3: Create Backup

Backup current files:
```bash
cd /opt/scrapping
mkdir -p backups/$(date +%Y%m%d)
cp -r *.py backups/$(date +%Y%m%d)/ 2>/dev/null || true
cp requirements.txt backups/$(date +%Y%m%d)/ 2>/dev/null || true
cp availability.db backups/$(date +%Y%m%d)/ 2>/dev/null || true
```

### Step 4: Upload Files to Server

You have several options for uploading files:

#### Option A: Using SCP (from your local computer)

```bash
# Upload a single file
scp path/to/updated_file.py username@your-server-ip:/opt/scrapping/

# Upload multiple files
scp path/to/*.py username@your-server-ip:/opt/scrapping/

# Upload entire directory (be careful!)
scp -r path/to/updated_folder username@your-server-ip:/opt/scrapping/
```

#### Option B: Using SFTP

1. Connect via SFTP:
   ```bash
   sftp username@your-server-ip
   ```

2. Navigate to application directory:
   ```bash
   cd /opt/scrapping
   ```

3. Upload files:
   ```bash
   put local_file.py
   put -r local_directory
   ```

4. Exit:
   ```bash
   exit
   ```

#### Option C: Using File Manager (if available)

If your server has a web-based file manager (like cPanel File Manager), use that to upload files directly.

#### Option D: Manual Copy-Paste (for small files)

1. SSH into server
2. Create/edit file:
   ```bash
   nano /opt/scrapping/updated_file.py
   ```
3. Paste content, save (Ctrl+X, Y, Enter)

### Step 5: Verify Files Are in Place

Check that uploaded files are in the correct location:

```bash
cd /opt/scrapping
ls -la *.py
```

Make sure file permissions are correct:
```bash
sudo chown -R $USER:$USER /opt/scrapping
```

### Step 6: Update Python Dependencies

If `requirements.txt` was updated:

```bash
cd /opt/scrapping
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**What this does**: Installs any new or updated Python packages.

### Step 7: Update Playwright Browsers (if needed)

Only if browser-related files were updated:

```bash
source venv/bin/activate
python -m playwright install chromium
```

### Step 8: Restart Services

Restart all services to apply changes:

```bash
sudo systemctl daemon-reload
sudo systemctl restart backend-scraper-flask
sudo systemctl restart backend-scraper-celery-worker
sudo systemctl restart backend-scraper-celery-beat
```

**What this does**: Stops and restarts all services so they use the new code.

### Step 9: Verify Update

Check that services restarted successfully:

```bash
sudo systemctl status backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

All should show "active (running)".

### Step 10: Check Logs

View recent logs to ensure everything is working:

```bash
sudo journalctl -u backend-scraper-flask -n 20
sudo journalctl -u backend-scraper-celery-worker -n 20
```

Look for any error messages.

---

## Updating the Frontend

If the frontend (React application) has been updated, you need to rebuild it.

### Step 1: Navigate to Frontend Directory

```bash
cd /opt/scrapping/frontend
```

### Step 2: Update Frontend Files

**If using Git**:
```bash
git pull
```

**If using file upload**: Upload the updated frontend files to `/opt/scrapping/frontend/`

### Step 3: Install/Update Dependencies

```bash
npm install
```

**What this does**: Installs or updates JavaScript packages needed by the frontend.

### Step 4: Set API Endpoint

Make sure the API endpoint is configured. Check or create `.env.production`:

```bash
nano .env.production
```

Should contain (replace with your server IP):
```
VITE_API_BASE=http://YOUR_SERVER_IP:8010/api
```

### Step 5: Build Frontend

```bash
npm run build
```

**What this does**: Compiles the React application into static files in the `dist` folder.

**Note**: This may take 1-2 minutes.

### Step 6: Reload Web Server

**If using Nginx**:
```bash
sudo nginx -s reload
```

**If using Flask to serve static files**:
```bash
sudo systemctl restart backend-scraper-flask
```

### Step 7: Clear Browser Cache

After updating the frontend, users should:
- Hard refresh the page: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Or clear browser cache

---

## After Updating

### 1. Verify Services Are Running

```bash
sudo systemctl status backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

### 2. Test the Application

1. **Test Backend API**:
   ```bash
   curl http://localhost:8010/api/health
   ```
   Should return JSON with status information.

2. **Test Frontend**:
   - Open browser: `http://YOUR_SERVER_IP`
   - Try searching for availability
   - Verify data loads correctly

### 3. Monitor Logs

Watch logs for a few minutes to ensure no errors:

```bash
sudo journalctl -u backend-scraper-flask -f
```

Press `Ctrl+C` to exit.

### 4. Check Scraping is Working

Verify that scraping tasks are running:

```bash
sudo journalctl -u backend-scraper-celery-worker -n 50 | grep -i "task\|scrape\|refresh"
```

You should see messages about tasks being executed.

---

## Troubleshooting Updates

### Problem: Services Won't Start After Update

**Symptoms**: Services show "failed" status after restart

**Solutions**:

1. **Check for syntax errors in code**:
   ```bash
   cd /opt/scrapping
   source venv/bin/activate
   python -m py_compile app.py
   ```
   If errors appear, the code has syntax issues.

2. **Check service logs for specific errors**:
   ```bash
   sudo journalctl -u backend-scraper-flask -n 50
   ```
   Look for error messages in red.

3. **Check if dependencies are missing**:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Restore from backup** (if update broke things):
   ```bash
   cd /opt/scrapping
   cp backups/YYYYMMDD/*.py .  # Restore Python files
   sudo systemctl restart backend-scraper-flask
   ```

### Problem: "Module not found" Errors

**Symptoms**: Logs show "ModuleNotFoundError" or "ImportError"

**Solutions**:

1. **Reinstall dependencies**:
   ```bash
   cd /opt/scrapping
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Check if new packages were added to requirements.txt**:
   ```bash
   cat requirements.txt
   ```

### Problem: Database Migration Errors

**Symptoms**: Errors about database schema or tables

**Solutions**:

1. **Backup database first**:
   ```bash
   cp /opt/scrapping/availability.db /opt/scrapping/availability.db.backup
   ```

2. **Check if database initialization is needed**:
   ```bash
   cd /opt/scrapping
   source venv/bin/activate
   python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

3. **If errors persist, contact support** - database migrations may be required.

### Problem: Frontend Shows Old Version

**Symptoms**: Browser still shows old interface after update

**Solutions**:

1. **Clear browser cache**:
   - Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
   - Or clear browser cache in settings

2. **Verify frontend was rebuilt**:
   ```bash
   ls -la /opt/scrapping/frontend/dist
   ```
   Check the modification date - should be recent.

3. **Rebuild frontend**:
   ```bash
   cd /opt/scrapping/frontend
   npm run build
   ```

4. **Reload web server**:
   ```bash
   sudo nginx -s reload
   # or
   sudo systemctl restart backend-scraper-flask
   ```

### Problem: Git Pull Conflicts

**Symptoms**: Git shows "merge conflict" or "your local changes would be overwritten"

**Solutions**:

1. **See what files have local changes**:
   ```bash
   git status
   ```

2. **Option A: Stash local changes** (saves them for later):
   ```bash
   git stash
   git pull
   git stash pop  # Reapply your changes
   ```

3. **Option B: Discard local changes** (if you don't need them):
   ```bash
   git reset --hard
   git pull
   ```
   **Warning**: This permanently deletes local changes!

4. **Option C: Create a backup branch**:
   ```bash
   git branch backup-$(date +%Y%m%d)
   git reset --hard
   git pull
   ```

### Problem: Port Already in Use

**Symptoms**: Service fails to start, logs show "Address already in use"

**Solutions**:

1. **Find what's using the port**:
   ```bash
   sudo netstat -tlnp | grep 8010
   # or
   sudo ss -tlnp | grep 8010
   ```

2. **Kill the process** (if it's an old instance):
   ```bash
   sudo kill -9 <PID>
   ```
   Replace `<PID>` with the process ID from step 1.

3. **Restart the service**:
   ```bash
   sudo systemctl restart backend-scraper-flask
   ```

### Problem: Permission Denied Errors

**Symptoms**: "Permission denied" when trying to update files

**Solutions**:

1. **Check file ownership**:
   ```bash
   ls -la /opt/scrapping
   ```

2. **Fix ownership** (replace `username` with your username):
   ```bash
   sudo chown -R username:username /opt/scrapping
   ```

3. **Check file permissions**:
   ```bash
   chmod +x /opt/scrapping/*.sh
   ```

### Rolling Back an Update

If an update causes problems and you need to go back:

1. **Stop services**:
   ```bash
   sudo systemctl stop backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
   ```

2. **Restore files from backup**:
   ```bash
   cd /opt/scrapping
   cp backups/YYYYMMDD/*.py .
   cp backups/YYYYMMDD/requirements.txt . 2>/dev/null || true
   ```

3. **Restore database** (if needed):
   ```bash
   cp backups/YYYYMMDD/availability.db availability.db
   ```

4. **Reinstall old dependencies** (if requirements.txt changed):
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Start services**:
   ```bash
   sudo systemctl start backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
   ```

---

## Update Checklist

Use this checklist each time you update:

- [ ] Created database backup
- [ ] Checked current service status (all running)
- [ ] Updated code (Git pull or file upload)
- [ ] Updated Python dependencies (`pip install -r requirements.txt`)
- [ ] Updated Playwright browsers (if needed)
- [ ] Restarted all services
- [ ] Verified services are running
- [ ] Checked logs for errors
- [ ] Tested backend API
- [ ] Tested frontend (if updated)
- [ ] Verified scraping is working
- [ ] Documented any issues encountered

---

## Quick Reference

**Git Update (Quick)**:
```bash
cd /opt/scrapping
git pull
source venv/bin/activate
pip install -r requirements.txt
bash update_server.sh
```

**File Upload Update (Quick)**:
```bash
cd /opt/scrapping
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
```

**Frontend Update**:
```bash
cd /opt/scrapping/frontend
npm install
npm run build
sudo nginx -s reload  # or restart Flask if using Flask
```

**Check Update Status**:
```bash
sudo systemctl status backend-scraper-flask backend-scraper-celery-worker backend-scraper-celery-beat
sudo journalctl -u backend-scraper-flask -n 20
```

---

**End of Update Guide**

For initial deployment instructions, see `DEPLOYMENT_GUIDE.md`.
