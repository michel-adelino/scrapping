# Quick Reference - Ubuntu Server Commands

## Service Management

### Reload Systemd After Modifying Service Files
```bash
# After editing service files in /etc/systemd/system/
sudo systemctl daemon-reload

# Then restart the service
sudo systemctl restart scrapping-celery-worker
```

### Start All Services
```bash
sudo systemctl start scrapping-flask scrapping-celery-worker scrapping-celery-beat scrapping-frontend
```

### Stop All Services
```bash
sudo systemctl stop scrapping-flask scrapping-celery-worker scrapping-celery-beat scrapping-frontend
```

### Restart All Services
```bash
sudo systemctl restart scrapping-flask scrapping-celery-worker scrapping-celery-beat scrapping-frontend
```

### Check Status
```bash
sudo systemctl status scrapping-flask
sudo systemctl status scrapping-celery-worker
sudo systemctl status scrapping-celery-beat
sudo systemctl status scrapping-frontend
```

### Enable Auto-Start on Boot
```bash
sudo systemctl enable scrapping-flask scrapping-celery-worker scrapping-celery-beat scrapping-frontend
```

## View Logs

All systemd service logs are stored in the systemd journal. Use `journalctl` to view them.

### Real-time Logs (Follow Mode)
```bash
# Flask Backend
sudo journalctl -u scrapping-flask -f

# Celery Worker
sudo journalctl -u scrapping-celery-worker -f

# Celery Beat
sudo journalctl -u scrapping-celery-beat -f

# Frontend
sudo journalctl -u scrapping-frontend -f
```

### View Last N Lines
```bash
# Last 100 lines
sudo journalctl -u scrapping-flask -n 100
sudo journalctl -u scrapping-celery-worker -n 100

# Last 50 lines
sudo journalctl -u scrapping-celery-worker -n 50
```

### Logs by Time Range
```bash
# Logs since today
sudo journalctl -u scrapping-flask --since today

# Logs since yesterday
sudo journalctl -u scrapping-flask --since yesterday

# Logs since specific time
sudo journalctl -u scrapping-flask --since "2025-11-30 07:00:00"

# Logs between two times
sudo journalctl -u scrapping-flask --since "2025-11-30 07:00:00" --until "2025-11-30 08:00:00"
```

### View All Logs (No Filter)
```bash
# All logs for a service
sudo journalctl -u scrapping-flask

# All logs with timestamps
sudo journalctl -u scrapping-flask --no-pager
```

### Search Logs
```bash
# Search for specific text
sudo journalctl -u scrapping-celery-worker | grep "error"

# Case-insensitive search
sudo journalctl -u scrapping-flask | grep -i "exception"
```

### Export Logs to File
```bash
# Export to file
sudo journalctl -u scrapping-flask > flask_logs.txt

# Export last 1000 lines
sudo journalctl -u scrapping-celery-worker -n 1000 > worker_logs.txt
```

### Log File Location
Systemd logs are stored in:
- **Journal files**: `/var/log/journal/` (if persistent logging is enabled)
- **Runtime logs**: `/run/log/journal/` (temporary, cleared on reboot)

**Note**: You typically don't access these files directly. Use `journalctl` instead.

## Update Application

```bash
cd /opt/scrapping

# Pull latest code (if using Git)
git pull

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# Update frontend dependencies
cd frontend
npm install

# Restart services
sudo systemctl restart scrapping-flask scrapping-celery-worker scrapping-celery-beat
```

## Troubleshooting

### Check if Services are Running
```bash
sudo systemctl status scrapping-flask scrapping-celery-worker scrapping-celery-beat scrapping-frontend
```

### Check Ports
```bash
sudo netstat -tlnp | grep -E '3000|8010|6379'
# or
sudo ss -tlnp | grep -E '3000|8010|6379'
```

### Test Redis
```bash
redis-cli ping
```

### Test Database
```bash
cd /opt/scrapping
source venv/bin/activate
python3 -c "from app import app, db; app.app_context().push(); print('OK')"
```

### Check Chrome/Chromium
```bash
chromium-browser --version
which chromium-browser
```

## Database Backup

### PostgreSQL
```bash
sudo -u postgres pg_dump scrapping_db > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
sudo -u postgres psql scrapping_db < backup_YYYYMMDD.sql
```

## Firewall

### Check Status
```bash
sudo ufw status
```

### Allow Ports
```bash
sudo ufw allow 3000/tcp
sudo ufw allow 8010/tcp
```

## File Locations

- Application: `/opt/scrapping`
- Logs: `sudo journalctl -u service-name`
- Environment: `/opt/scrapping/.env`
- Service Files: `/etc/systemd/system/scrapping-*.service`

