#!/bin/bash

# Quick Update Script for VPS Server
# Run this after git pull to update the application
# Usage: bash update_server.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
APP_DIR="/opt/scrapping"
APP_USER=$(whoami)

echo -e "${GREEN}=========================================="
echo "Updating Backend Scraper Application"
echo "==========================================${NC}"
echo ""

# Check if we're in the app directory
if [ ! -f "$APP_DIR/app.py" ]; then
    echo -e "${RED}Error: app.py not found in $APP_DIR${NC}"
    echo "Please run this script from $APP_DIR or ensure the app is installed there"
    exit 1
fi

cd $APP_DIR

echo -e "${GREEN}Step 1: Updating Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Step 2: Updating Playwright browsers (if needed)...${NC}"
source venv/bin/activate
python -m playwright install chromium || echo -e "${YELLOW}Playwright browser update skipped (may already be up to date)${NC}"

echo -e "${GREEN}Step 3: Updating systemd service files...${NC}"
# Flask service
sudo tee /etc/systemd/system/backend-scraper-flask.service > /dev/null << EOF
[Unit]
Description=Backend Scraper Flask Application
After=network.target redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery Worker service
sudo tee /etc/systemd/system/backend-scraper-celery-worker.service > /dev/null << EOF
[Unit]
Description=Backend Scraper Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python3 -m celery -A celery_app worker --pool=prefork --concurrency=10 --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery Beat service
sudo tee /etc/systemd/system/backend-scraper-celery-beat.service > /dev/null << EOF
[Unit]
Description=Backend Scraper Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python3 -m celery -A celery_app beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Step 4: Reloading systemd and restarting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl restart backend-scraper-flask.service
sudo systemctl restart backend-scraper-celery-worker.service
sudo systemctl restart backend-scraper-celery-beat.service

echo ""
echo -e "${GREEN}=========================================="
echo "Update Complete!"
echo "==========================================${NC}"
echo ""
echo "Check service status:"
echo "  sudo systemctl status backend-scraper-flask"
echo "  sudo systemctl status backend-scraper-celery-worker"
echo "  sudo systemctl status backend-scraper-celery-beat"
echo ""
echo "View logs:"
echo "  sudo journalctl -u backend-scraper-flask -f"
echo "  sudo journalctl -u backend-scraper-celery-worker -f"
echo "  sudo journalctl -u backend-scraper-celery-beat -f"
echo ""
