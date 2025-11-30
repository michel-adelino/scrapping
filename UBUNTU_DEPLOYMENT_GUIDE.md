# Complete Ubuntu Server Deployment Guide

This guide will walk you through deploying your Flask + Celery + React application on an Ubuntu server.

## Prerequisites

- Ubuntu 20.04 LTS or later (22.04 LTS recommended)
- Root or sudo access
- At least 2GB RAM (4GB+ recommended)
- Internet connection

---

## Step 1: Initial Server Setup

### 1.1 Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Install Essential Tools

```bash
sudo apt install -y curl wget git build-essential software-properties-common
```

---

## Step 2: Install Python and Dependencies

### 2.1 Install Python 3.10+ and pip

```bash
sudo apt install -y python3 python3-pip python3-venv
```

Verify installation:
```bash
python3 --version
pip3 --version
```

### 2.2 Install PostgreSQL (or SQLite if you prefer)

**Option A: PostgreSQL (Recommended for Production)**
```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

Create database and user:
```bash
sudo -u postgres psql
```

In PostgreSQL prompt:
```sql
CREATE DATABASE scrapping_db;
CREATE USER scrapping_user WITH PASSWORD 'scrapping_pwd';
GRANT ALL PRIVILEGES ON DATABASE scrapping_db TO scrapping_user;
\q
```

**Important for PostgreSQL 15+:** Grant schema permissions (required for creating tables):
```bash
sudo -u postgres psql -d scrapping_db
```

In PostgreSQL prompt:
```sql
GRANT USAGE ON SCHEMA public TO scrapping_user;
GRANT CREATE ON SCHEMA public TO scrapping_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scrapping_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scrapping_user;
\q
```

**Option B: SQLite (Simpler, for testing)**
```bash
# SQLite comes pre-installed with Python
# No additional setup needed
```

---

## Step 3: Install Redis

### 3.1 Install Redis Server

```bash
sudo apt install -y redis-server
```

### 3.2 Configure Redis

Edit Redis config:
```bash
sudo nano /etc/redis/redis.conf
```

Find and modify:
```
# Change: bind 127.0.0.1
# To: bind 127.0.0.1 ::1
# (Keep it localhost for security)

# Set max memory (optional, adjust based on your server)
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 3.3 Start and Enable Redis

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server
```

Test Redis:
```bash
redis-cli ping
# Should return: PONG
```

---

## Step 4: Install Chrome/Chromium for Selenium

### 4.1 Install Chromium and Dependencies

```bash
sudo apt install -y chromium-browser chromium-chromedriver
```

Or install Google Chrome:
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

### 4.2 Install Additional Dependencies for Headless Chrome

**For Ubuntu 22.04 and earlier:**
```bash
sudo apt install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

**For Ubuntu 24.04 and later:**
```bash
sudo apt install -y \
    libnss3 \
    libatk-bridge2.0-0t64 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64
```

**Or use this command that works for both versions:**
```bash
sudo apt install -y \
    libnss3 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1

# Handle package name differences between Ubuntu versions
if apt-cache show libatk-bridge2.0-0t64 > /dev/null 2>&1; then
    sudo apt install -y libatk-bridge2.0-0t64 libasound2t64
else
    sudo apt install -y libatk-bridge2.0-0 libasound2
fi
```

### 4.3 Verify Chrome Installation

```bash
chromium-browser --version
# or
google-chrome --version
```

---

## Step 5: Install Node.js and npm

### 5.1 Install Node.js 20 LTS (using NodeSource)

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**Alternative: Install Node.js 22 LTS (if you prefer the latest LTS)**
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

Verify:
```bash
node --version
npm --version
```

---

## Step 6: Deploy Your Application

### 6.1 Create Application Directory

```bash
sudo mkdir -p /opt/scrapping
sudo chown $USER:$USER /opt/scrapping
cd /opt/scrapping
```

### 6.2 Upload Your Project Files

**Option A: Using Git (Recommended)**
```bash
git clone <your-repository-url> .
```

**Option B: Using SCP (from your local machine)**
```bash
# On your local machine:
scp -r /path/to/scrapping/* user@your-server-ip:/opt/scrapping/
```

**Option C: Using rsync**
```bash
# On your local machine:
rsync -avz --exclude 'venv' --exclude 'node_modules' \
  /path/to/scrapping/ user@your-server-ip:/opt/scrapping/
```

### 6.3 Set Up Python Virtual Environment

```bash
cd /opt/scrapping
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6.4 Set Up Frontend Dependencies

```bash
cd /opt/scrapping/frontend
npm install
```

---

## Step 7: Configure Environment Variables

### 7.1 Create Environment File

```bash
cd /opt/scrapping
nano .env
```

Add the following (adjust as needed):
```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=8010

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://scrapping_user:your_secure_password@localhost:5432/scrapping_db

# Or for SQLite:
# DATABASE_URL=sqlite:///scrapping.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Chrome Binary (if needed)
CHROME_BINARY=/usr/bin/chromium-browser
# or
# CHROME_BINARY=/usr/bin/google-chrome
```

### 7.2 Update app.py to Load Environment Variables

If your app.py doesn't already load `.env`, you may need to add:
```python
from dotenv import load_dotenv
load_dotenv()
```

And install python-dotenv:
```bash
source venv/bin/activate
pip install python-dotenv
```

---

## Step 8: Initialize Database

### 8.1 Create Database Tables

```bash
cd /opt/scrapping
source venv/bin/activate
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## Step 9: Create Systemd Service Files

### 9.1 Create Flask Service

```bash
sudo nano /etc/systemd/system/scrapping-flask.service
```

Add:
```ini
[Unit]
Description=Scrapping Flask Application
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/opt/scrapping
Environment="PATH=/opt/scrapping/venv/bin"
ExecStart=/opt/scrapping/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `your_username` with your actual Ubuntu username.

### 9.2 Create Celery Worker Service

```bash
sudo nano /etc/systemd/system/scrapping-celery-worker.service
```

Add:
```ini
[Unit]
Description=Scrapping Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/opt/scrapping
Environment="PATH=/opt/scrapping/venv/bin"
ExecStart=/opt/scrapping/venv/bin/python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9.3 Create Celery Beat Service

```bash
sudo nano /etc/systemd/system/scrapping-celery-beat.service
```

Add:
```ini
[Unit]
Description=Scrapping Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/opt/scrapping
Environment="PATH=/opt/scrapping/venv/bin"
ExecStart=/opt/scrapping/venv/bin/python -m celery -A celery_app beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9.4 Create Frontend Service (Optional - for production, use Nginx)

```bash
sudo nano /etc/systemd/system/scrapping-frontend.service
```

Add:
```ini
[Unit]
Description=Scrapping Frontend (Vite)
After=network.target

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/opt/scrapping/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note:** For production, you should build the frontend and serve it with Nginx instead.

---

## Step 10: Enable and Start Services

### 10.1 Reload Systemd

```bash
sudo systemctl daemon-reload
```

### 10.2 Enable Services (Start on Boot)

```bash
sudo systemctl enable scrapping-flask.service
sudo systemctl enable scrapping-celery-worker.service
sudo systemctl enable scrapping-celery-beat.service
sudo systemctl enable scrapping-frontend.service  # Optional
```

### 10.3 Start Services

```bash
sudo systemctl start scrapping-flask.service
sudo systemctl start scrapping-celery-worker.service
sudo systemctl start scrapping-celery-beat.service
sudo systemctl start scrapping-frontend.service  # Optional
```

### 10.4 Check Service Status

```bash
sudo systemctl status scrapping-flask.service
sudo systemctl status scrapping-celery-worker.service
sudo systemctl status scrapping-celery-beat.service
sudo systemctl status scrapping-frontend.service
```

### 10.5 View Logs

```bash
# View logs
sudo journalctl -u scrapping-flask.service -f
sudo journalctl -u scrapping-celery-worker.service -f
sudo journalctl -u scrapping-celery-beat.service -f

# View last 100 lines
sudo journalctl -u scrapping-flask.service -n 100
```

---

## Step 11: Configure Firewall

### 11.1 Install and Configure UFW

```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8010/tcp  # Backend API
sudo ufw enable
sudo ufw status
```

---

## Step 12: Test Your Application

### 12.1 Check if Services are Running

```bash
# Check all services
sudo systemctl status scrapping-flask scrapping-celery-worker scrapping-celery-beat scrapping-frontend

# Check ports
sudo netstat -tlnp | grep -E '3000|8010|6379'
```

### 12.2 Test API Endpoint

```bash
curl http://localhost:8010/api/health
# or
curl http://YOUR_SERVER_IP:8010/api/health
```

### 12.3 Access Frontend

Open in browser:
- Frontend: `http://YOUR_SERVER_IP:3000`
- Backend API: `http://YOUR_SERVER_IP:8010/api`

---

## Step 13: Production Optimization (Optional but Recommended)

### 13.1 Install and Configure Nginx (Reverse Proxy)

```bash
sudo apt install -y nginx
```

Create Nginx config:
```bash
sudo nano /etc/nginx/sites-available/scrapping
```

Add:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/scrapping /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Update firewall:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 13.2 Set Up SSL with Let's Encrypt (Optional)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 13.3 Build Frontend for Production

```bash
cd /opt/scrapping/frontend
npm run build
```

Then update Nginx to serve static files:
```nginx
location / {
    root /opt/scrapping/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

---

## Step 14: Useful Management Commands

### 14.1 Service Management

```bash
# Start services
sudo systemctl start scrapping-flask
sudo systemctl start scrapping-celery-worker
sudo systemctl start scrapping-celery-beat

# Stop services
sudo systemctl stop scrapping-flask
sudo systemctl stop scrapping-celery-worker
sudo systemctl stop scrapping-celery-beat

# Restart services
sudo systemctl restart scrapping-flask
sudo systemctl restart scrapping-celery-worker
sudo systemctl restart scrapping-celery-beat

# Check status
sudo systemctl status scrapping-flask
```

### 14.2 View Logs

```bash
# Real-time logs
sudo journalctl -u scrapping-flask -f
sudo journalctl -u scrapping-celery-worker -f
sudo journalctl -u scrapping-celery-beat -f

# Last 50 lines
sudo journalctl -u scrapping-flask -n 50

# Logs since today
sudo journalctl -u scrapping-flask --since today
```

### 14.3 Update Application

```bash
cd /opt/scrapping

# Pull latest changes (if using Git)
git pull

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# Update frontend dependencies
cd frontend
npm install

# Restart services
sudo systemctl restart scrapping-flask
sudo systemctl restart scrapping-celery-worker
sudo systemctl restart scrapping-celery-beat
```

---

## Step 15: Troubleshooting

### 15.1 Check Service Logs

```bash
sudo journalctl -u scrapping-flask.service -n 100 --no-pager
```

### 15.2 Check if Ports are in Use

```bash
sudo lsof -i :8010
sudo lsof -i :3000
sudo lsof -i :6379
```

### 15.3 Test Redis Connection

```bash
redis-cli ping
```

### 15.4 Test Database Connection

```bash
cd /opt/scrapping
source venv/bin/activate
python3 -c "from app import app, db; app.app_context().push(); print('Database OK')"
```

### 15.5 Check Chrome/Chromium

```bash
chromium-browser --version
which chromium-browser
```

### 15.6 Common Issues

**Issue: Service fails to start**
- Check logs: `sudo journalctl -u service-name -n 50`
- Verify file paths in service files
- Check permissions: `ls -la /opt/scrapping`

**Issue: Port already in use**
- Find process: `sudo lsof -i :PORT`
- Kill process: `sudo kill -9 PID`

**Issue: Redis connection refused**
- Check Redis: `sudo systemctl status redis-server`
- Test: `redis-cli ping`

**Issue: Database connection error**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `.env` file
- Test connection: `psql -U scrapping_user -d scrapping_db`

---

## Quick Start Summary

After initial setup, to start everything:

```bash
sudo systemctl start scrapping-flask
sudo systemctl start scrapping-celery-worker
sudo systemctl start scrapping-celery-beat
sudo systemctl start scrapping-frontend  # Optional
```

To stop everything:

```bash
sudo systemctl stop scrapping-flask
sudo systemctl stop scrapping-celery-worker
sudo systemctl stop scrapping-celery-beat
sudo systemctl stop scrapping-frontend
```

---

## Security Checklist

- [ ] Change default database passwords
- [ ] Use strong passwords for all services
- [ ] Configure firewall (UFW)
- [ ] Set up SSL/HTTPS (Let's Encrypt)
- [ ] Use environment variables for secrets
- [ ] Restrict database access (PostgreSQL)
- [ ] Keep system and packages updated
- [ ] Set up regular backups
- [ ] Monitor logs regularly
- [ ] Use non-root user for services

---

## Backup Strategy

### Database Backup

```bash
# PostgreSQL
sudo -u postgres pg_dump scrapping_db > backup_$(date +%Y%m%d).sql

# SQLite
cp /opt/scrapping/scrapping.db /opt/scrapping/backups/scrapping_$(date +%Y%m%d).db
```

### Application Backup

```bash
tar -czf scrapping_backup_$(date +%Y%m%d).tar.gz /opt/scrapping
```

---

## Monitoring (Optional)

Consider setting up monitoring tools:
- **PM2** for process management (alternative to systemd)
- **Supervisor** for process control
- **Log rotation** with logrotate
- **System monitoring** with htop/glances

---

## Next Steps

1. Set up automated backups
2. Configure log rotation
3. Set up monitoring and alerts
4. Configure domain name and DNS
5. Set up SSL certificate
6. Optimize database performance
7. Set up CI/CD pipeline

---

**Need Help?** Check the logs first, then review the troubleshooting section above.

