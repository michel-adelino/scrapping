#!/bin/bash
# Fix frontend to use production build with Nginx instead of dev server

set -e

APP_DIR="/opt/scrapping"
FRONTEND_DIR="$APP_DIR/frontend"

echo "Fixing frontend for production..."

# Stop the failing frontend service
echo "Stopping frontend dev server service..."
sudo systemctl stop scrapping-frontend.service 2>/dev/null || true
sudo systemctl disable scrapping-frontend.service 2>/dev/null || true

# Build the frontend
echo "Building frontend for production..."
cd $FRONTEND_DIR

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "Building frontend..."
npm run build

if [ ! -d "dist" ]; then
    echo "ERROR: Build failed - dist directory not found"
    exit 1
fi

echo "✓ Frontend built successfully"

# Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Create Nginx configuration
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/scrapping-frontend > /dev/null << EOF
server {
    listen 3000;
    server_name _;

    root $FRONTEND_DIR/dist;
    index index.html;

    # Serve static files
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Proxy API requests to Flask backend
    location /api {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/scrapping-frontend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Test and restart Nginx
echo "Testing Nginx configuration..."
sudo nginx -t

echo "Starting Nginx..."
sudo systemctl enable nginx
sudo systemctl restart nginx

# Update firewall if needed
sudo ufw allow 3000/tcp 2>/dev/null || true

echo ""
echo "✓ Frontend is now served via Nginx (production mode)"
echo "✓ Frontend available at: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "To rebuild frontend after code changes:"
echo "  cd $FRONTEND_DIR && npm run build && sudo systemctl reload nginx"
echo ""
echo "Check Nginx status:"
echo "  sudo systemctl status nginx"

