#!/bin/bash

# Ubuntu Server Setup Script for Scrapping Application
# Run this script with: bash setup_ubuntu_server.sh

set -e  # Exit on error

echo "=========================================="
echo "Ubuntu Server Setup for Scrapping App"
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

echo -e "${GREEN}Step 4: Installing PostgreSQL...${NC}"
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo -e "${YELLOW}Creating PostgreSQL database and user...${NC}"
echo "Please enter a password for the database user 'scrapping_user':"
read -s DB_PASSWORD
sudo -u postgres psql -c "CREATE DATABASE scrapping_db;" || echo "Database may already exist"
sudo -u postgres psql -c "CREATE USER scrapping_user WITH PASSWORD '$DB_PASSWORD';" || echo "User may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE scrapping_db TO scrapping_user;"

echo -e "${GREEN}Step 5: Installing Redis...${NC}"
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping

echo -e "${GREEN}Step 6: Installing Chromium and dependencies...${NC}"
sudo apt install -y chromium-browser chromium-chromedriver
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

echo -e "${GREEN}Step 7: Installing Node.js...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version

echo -e "${GREEN}Step 8: Creating application directory...${NC}"
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

echo -e "${YELLOW}Step 9: Please copy your project files to $APP_DIR${NC}"
echo "You can use:"
echo "  - Git: cd $APP_DIR && git clone <your-repo> ."
echo "  - SCP: scp -r /path/to/scrapping/* $APP_USER@$(hostname -I | awk '{print $1}'):$APP_DIR/"
echo ""
read -p "Press Enter after you've copied the files to continue..."

if [ ! -f "$APP_DIR/app.py" ]; then
    echo -e "${RED}Error: app.py not found in $APP_DIR${NC}"
    echo "Please copy your project files and run this script again."
    exit 1
fi

echo -e "${GREEN}Step 10: Setting up Python virtual environment...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install python-dotenv  # For .env file support

echo -e "${GREEN}Step 11: Setting up frontend dependencies...${NC}"
cd $APP_DIR/frontend
npm install

echo -e "${GREEN}Step 12: Creating .env file...${NC}"
cd $APP_DIR
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=8010

# Database Configuration
DATABASE_URL=postgresql://scrapping_user:$DB_PASSWORD@localhost:5432/scrapping_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Chrome Binary
CHROME_BINARY=/usr/bin/chromium-browser
EOF
    echo -e "${GREEN}.env file created${NC}"
else
    echo -e "${YELLOW}.env file already exists, skipping...${NC}"
fi

echo -e "${GREEN}Step 13: Initializing database...${NC}"
cd $APP_DIR
source venv/bin/activate
python3 -c "from app import app, db; app.app_context().push(); db.create_all()" || echo "Database initialization may have failed - check manually"

echo -e "${GREEN}Step 14: Creating systemd service files...${NC}"

# Flask service
sudo tee /etc/systemd/system/scrapping-flask.service > /dev/null << EOF
[Unit]
Description=Scrapping Flask Application
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery Worker service
sudo tee /etc/systemd/system/scrapping-celery-worker.service > /dev/null << EOF
[Unit]
Description=Scrapping Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery Beat service
sudo tee /etc/systemd/system/scrapping-celery-beat.service > /dev/null << EOF
[Unit]
Description=Scrapping Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python -m celery -A celery_app beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
sudo tee /etc/systemd/system/scrapping-frontend.service > /dev/null << EOF
[Unit]
Description=Scrapping Frontend (Vite)
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Step 15: Enabling and starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable scrapping-flask.service
sudo systemctl enable scrapping-celery-worker.service
sudo systemctl enable scrapping-celery-beat.service
sudo systemctl enable scrapping-frontend.service

echo -e "${GREEN}Step 16: Configuring firewall...${NC}"
sudo apt install -y ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8010/tcp  # Backend API
echo "y" | sudo ufw enable
sudo ufw status

echo -e "${GREEN}Step 17: Starting services...${NC}"
sudo systemctl start scrapping-flask.service
sudo systemctl start scrapping-celery-worker.service
sudo systemctl start scrapping-celery-beat.service
sudo systemctl start scrapping-frontend.service

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Check service status:"
echo "  sudo systemctl status scrapping-flask"
echo "  sudo systemctl status scrapping-celery-worker"
echo "  sudo systemctl status scrapping-celery-beat"
echo "  sudo systemctl status scrapping-frontend"
echo ""
echo "View logs:"
echo "  sudo journalctl -u scrapping-flask -f"
echo ""
echo "Access your application:"
echo "  Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "  Backend:  http://$(hostname -I | awk '{print $1}'):8010"
echo ""
echo -e "${YELLOW}Note: Please review and update the .env file if needed.${NC}"
echo ""

