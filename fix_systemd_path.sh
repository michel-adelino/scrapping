#!/bin/bash
# Fix systemd service PATH to include system binaries
# This fixes the issue where xvfb-run can't find awk and getopt

set -e

APP_DIR="/opt/scrapping"
APP_USER="root"  # Change this if you're using a different user

echo "Fixing systemd service PATH configuration..."

# Fix Flask service
echo "Updating scrapping-flask.service..."
sudo tee /etc/systemd/system/scrapping-flask.service > /dev/null << EOF
[Unit]
Description=Scrapping Flask Application
After=network.target redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$APP_DIR/venv/bin"
ExecStart=/usr/bin/xvfb-run -a $APP_DIR/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Fix Celery Worker service
echo "Updating scrapping-celery-worker.service..."
sudo tee /etc/systemd/system/scrapping-celery-worker.service > /dev/null << EOF
[Unit]
Description=Scrapping Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$APP_DIR/venv/bin"
ExecStart=/usr/bin/xvfb-run -a $APP_DIR/venv/bin/python3 -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Fix Celery Beat service (doesn't use xvfb, but should still have proper PATH)
echo "Updating scrapping-celery-beat.service..."
sudo tee /etc/systemd/system/scrapping-celery-beat.service > /dev/null << EOF
[Unit]
Description=Scrapping Celery Beat Scheduler
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

echo ""
echo "✓ Service files updated"
echo ""
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "Restarting services..."
sudo systemctl restart scrapping-flask
sudo systemctl restart scrapping-celery-worker
sudo systemctl restart scrapping-celery-beat

echo ""
echo "Checking service status..."
sleep 2
sudo systemctl status scrapping-flask --no-pager -l

echo ""
echo "If services are running, you can check logs with:"
echo "  sudo journalctl -u scrapping-flask -f"
echo "  sudo journalctl -u scrapping-celery-worker -f"

