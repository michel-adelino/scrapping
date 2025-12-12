#!/bin/bash

# Ubuntu Server Setup Script for Backend Scraper Application
# Run this script with: bash setup_ubuntu_server.sh

set -e  # Exit on error

echo "=========================================="
echo "Ubuntu Server Setup for Backend Scraper"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please do not run as root. Run as a regular user with sudo privileges.${NC}"
   exit 1
fi

# Variables
APP_DIR="/opt/scrapping"
APP_USER=$(whoami)

echo -e "${GREEN}Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${GREEN}Step 2: Installing essential tools...${NC}"
sudo apt install -y curl wget git build-essential software-properties-common

echo -e "${GREEN}Step 3: Installing Python 3 and pip...${NC}"
sudo apt install -y python3 python3-pip python3-venv
python3 --version
pip3 --version

echo -e "${GREEN}Step 4: SQLite Database${NC}"
echo -e "${YELLOW}Using SQLite database (no installation needed)${NC}"
echo "Database file will be created at: $APP_DIR/availability.db"

echo -e "${GREEN}Step 5: Installing Redis...${NC}"
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping

echo -e "${GREEN}Step 6: Installing Google Chrome...${NC}"

# Remove snap Chromium if installed (snap version causes issues)
echo -e "${YELLOW}Removing snap Chromium if installed...${NC}"
sudo snap remove chromium 2>/dev/null || echo "No snap Chromium to remove"

# Remove apt Chromium packages if installed
echo -e "${YELLOW}Removing apt Chromium packages if installed...${NC}"
sudo apt purge chromium-browser chromium-chromedriver -y 2>/dev/null || echo "No apt Chromium to remove"

# Install Chrome dependencies (handle different Ubuntu versions)
echo -e "${YELLOW}Installing Chrome dependencies...${NC}"
# Try to install packages, handling Ubuntu 24.04+ package name changes
sudo apt install -y \
    libnss3 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    wget || true

# Handle package name differences between Ubuntu versions
# Ubuntu 24.04+ uses libatk-bridge2.0-0t64 and libasound2t64
# Older versions use libatk-bridge2.0-0 and libasound2
if apt-cache show libatk-bridge2.0-0t64 > /dev/null 2>&1; then
    echo "Installing Ubuntu 24.04+ packages..."
    sudo apt install -y libatk-bridge2.0-0t64 libasound2t64 || true
else
    echo "Installing older Ubuntu version packages..."
    sudo apt install -y libatk-bridge2.0-0 libasound2 || true
fi

# Download and install Google Chrome from official repository
echo -e "${GREEN}Downloading Google Chrome...${NC}"
cd /tmp
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb || {
    echo -e "${RED}Failed to download Google Chrome. Please check your internet connection.${NC}"
    exit 1
}

echo -e "${GREEN}Installing Google Chrome...${NC}"
sudo apt install ./google-chrome-stable_current_amd64.deb -y || {
    echo -e "${RED}Failed to install Google Chrome.${NC}"
    exit 1
}

# Clean up downloaded file
rm -f google-chrome-stable_current_amd64.deb

# Verify Google Chrome installation
if command -v google-chrome &> /dev/null; then
    echo -e "${GREEN}✓ Google Chrome installed successfully${NC}"
    google-chrome --version
else
    echo -e "${RED}✗ Google Chrome installation verification failed${NC}"
    exit 1
fi

# Note: xvfb is NOT needed for Playwright
# Playwright runs in headless mode by default on Linux (see browser_utils.py)
# Headless mode doesn't require a display server

echo -e "${GREEN}Step 7: Creating application directory...${NC}"
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

echo -e "${YELLOW}Step 8: Copying project files to $APP_DIR${NC}"
echo ""
echo "Option 1: If you're running this script from the scrapping folder, files will be copied automatically"
echo "Option 2: Copy files manually using one of these methods:"
echo "  - Git: cd $APP_DIR && git clone <your-repo> ."
echo "  - SCP: scp -r /path/to/scrapping/* $APP_USER@$(hostname -I | awk '{print $1}'):$APP_DIR/"
echo "  - Rsync: rsync -avz /path/to/scrapping/ $APP_USER@$(hostname -I | awk '{print $1}'):$APP_DIR/"
echo ""

# Try to auto-detect if we're in the scrapping directory
CURRENT_DIR=$(pwd)
if [ -f "$CURRENT_DIR/app.py" ] && [ -f "$CURRENT_DIR/requirements.txt" ]; then
    echo -e "${GREEN}Detected scrapping folder at $CURRENT_DIR${NC}"
    echo -e "${GREEN}Copying files to $APP_DIR...${NC}"
    sudo mkdir -p $APP_DIR
    sudo cp -r $CURRENT_DIR/* $APP_DIR/ 2>/dev/null || {
        echo -e "${YELLOW}Some files may have failed to copy. Continuing...${NC}"
    }
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
else
    echo -e "${YELLOW}Not in scrapping folder. Please copy files manually.${NC}"
    read -p "Press Enter after you've copied the files to continue..."
fi

if [ ! -f "$APP_DIR/app.py" ]; then
    echo -e "${RED}Error: app.py not found in $APP_DIR${NC}"
    echo "Please ensure the scrapping folder contents are in $APP_DIR"
    echo "You can copy them with: sudo cp -r /path/to/scrapping/* $APP_DIR/"
    exit 1
fi

echo -e "${GREEN}Step 9: Setting up Python virtual environment...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install python-dotenv  # For .env file support

# Install Playwright browsers
echo -e "${GREEN}Installing Playwright browsers...${NC}"
source venv/bin/activate
echo -e "${YELLOW}This may take a few minutes as it downloads browser binaries...${NC}"
python -m playwright install chromium || {
    echo -e "${RED}Error: Playwright browser installation failed!${NC}"
    echo -e "${YELLOW}Try running manually: cd $APP_DIR && source venv/bin/activate && python -m playwright install chromium${NC}"
    exit 1
}
echo -e "${GREEN}✓ Playwright browsers installed successfully${NC}"

echo -e "${GREEN}Step 10: Creating .env file...${NC}"
cd $APP_DIR
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=8010
FLASK_DEBUG=False

# Database Configuration (SQLite)
# Database file will be created at: $APP_DIR/availability.db
# Leave DATABASE_URL unset to use default SQLite database
# Or set it explicitly: DATABASE_URL=sqlite:///$APP_DIR/availability.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Chrome Binary (Google Chrome, not Chromium)
CHROME_BINARY=/usr/bin/google-chrome
EOF
    echo -e "${GREEN}.env file created${NC}"
else
    echo -e "${YELLOW}.env file already exists, skipping...${NC}"
fi

echo -e "${GREEN}Step 11: Initializing database...${NC}"
cd $APP_DIR
source venv/bin/activate
python3 -c "from app import app, db; app.app_context().push(); db.create_all()" || echo "Database initialization may have failed - check manually"

echo -e "${GREEN}Step 12: Creating systemd service files...${NC}"

# Flask service
# Playwright runs in headless mode by default on Linux, so xvfb-run is NOT needed
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
# Playwright runs in headless mode by default on Linux, so xvfb-run is NOT needed
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
# Does NOT use xvfb-run because Beat only schedules tasks, it doesn't execute them
# Beat doesn't use Playwright, so it doesn't need a virtual display
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

echo -e "${GREEN}Step 13: Enabling and starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable backend-scraper-flask.service
sudo systemctl enable backend-scraper-celery-worker.service
sudo systemctl enable backend-scraper-celery-beat.service

echo -e "${GREEN}Step 14: Configuring firewall...${NC}"
sudo apt install -y ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8010/tcp  # Backend API
echo "y" | sudo ufw enable
sudo ufw status

echo -e "${GREEN}Step 15: Configuring journald log limits...${NC}"
# Configure journald to limit log size and prevent disk fill
sudo tee -a /etc/systemd/journald.conf > /dev/null << 'JOURNALD_EOF'

# Limit journal size to prevent disk fill (added by setup script)
SystemMaxUse=1G
SystemKeepFree=2G
SystemMaxFileSize=100M
MaxRetentionSec=7day
JOURNALD_EOF
sudo systemctl restart systemd-journald
echo -e "${GREEN}Journald configured with 1GB size limit and 7-day retention${NC}"

echo -e "${GREEN}Step 16: Starting services...${NC}"
sudo systemctl start backend-scraper-flask.service
sudo systemctl start backend-scraper-celery-worker.service
sudo systemctl start backend-scraper-celery-beat.service

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
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
echo "Check journal size:"
echo "  sudo journalctl --disk-usage"
echo ""
echo "Clean old logs (if needed):"
echo "  sudo journalctl --vacuum-time=7d"
echo ""
echo "Access your application:"
echo "  Backend API:  http://$(hostname -I | awk '{print $1}'):8010"
echo ""
echo -e "${GREEN}Configuration Notes:${NC}"
echo "  - Celery Worker concurrency set to 10 (can be adjusted in service file)"
echo "  - Playwright runs in headless mode by default on Linux (no display needed)"
echo "  - Celery Beat automatically triggers first cycle on startup"
echo "  - Cycles continue automatically (each cycle triggers the next)"
echo ""
echo -e "${YELLOW}Note: Please review and update the .env file if needed.${NC}"
echo -e "${YELLOW}Debug mode is disabled by default. Set FLASK_DEBUG=True in .env for development only.${NC}"
echo ""

