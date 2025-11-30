#!/bin/bash
# Quick fix to install psycopg2-binary for PostgreSQL support

echo "Installing psycopg2-binary and python-dotenv..."

cd /opt/scrapping
source venv/bin/activate
pip install psycopg2-binary==2.9.9 python-dotenv==1.0.0

echo "Packages installed successfully!"
echo "Restarting Flask service..."
sudo systemctl restart scrapping-flask

echo "Check status with: sudo systemctl status scrapping-flask"

