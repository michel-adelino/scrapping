# Quick Reference - Ubuntu Server Commands

## Service Management

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

### Real-time Logs
```bash
sudo journalctl -u scrapping-flask -f
sudo journalctl -u scrapping-celery-worker -f
sudo journalctl -u scrapping-celery-beat -f
```

### Last 100 Lines
```bash
sudo journalctl -u scrapping-flask -n 100
```

### Logs Since Today
```bash
sudo journalctl -u scrapping-flask --since today
```

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

