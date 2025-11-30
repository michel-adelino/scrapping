#!/bin/bash
# Build frontend for production and configure Nginx to serve it

set -e

APP_DIR="/opt/scrapping"
FRONTEND_DIR="$APP_DIR/frontend"

echo "Building frontend for production..."

cd $FRONTEND_DIR

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build the frontend
echo "Building frontend..."
npm run build

echo "Frontend built successfully!"
echo "Build output is in: $FRONTEND_DIR/dist"

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Nginx is not installed. Installing..."
    sudo apt update
    sudo apt install -y nginx
fi

# Create Nginx configuration
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/scrapping-frontend > /dev/null << 'EOF'
server {
    listen 3000;
    server_name _;

    root /opt/scrapping/frontend/dist;
    index index.html;

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to Flask backend
    location /api {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/scrapping-frontend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site if exists

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

echo ""
echo "✓ Frontend built and served with Nginx"
echo "✓ Frontend available at: http://YOUR_SERVER_IP:3000"
echo "✓ API proxied at: http://YOUR_SERVER_IP:3000/api"
echo ""
echo "To rebuild frontend after changes, run:"
echo "  cd $FRONTEND_DIR && npm run build && sudo systemctl reload nginx"

