#!/bin/bash
# Fix missing dependencies for xvfb-run
# This script installs awk and getopt which are required by xvfb-run

set -e

echo "Installing missing dependencies for xvfb-run..."

# Install awk (gawk or mawk)
if ! command -v awk &> /dev/null; then
    echo "Installing awk (gawk)..."
    sudo apt update
    sudo apt install -y gawk
else
    echo "✓ awk is already installed"
fi

# Install getopt (part of util-linux)
if ! command -v getopt &> /dev/null; then
    echo "Installing getopt (util-linux)..."
    sudo apt update
    sudo apt install -y util-linux
else
    echo "✓ getopt is already installed"
fi

# Verify installations
echo ""
echo "Verifying installations..."
if command -v awk &> /dev/null && command -v getopt &> /dev/null; then
    echo "✓ All dependencies installed successfully"
    echo ""
    echo "Restarting Flask service..."
    sudo systemctl restart scrapping-flask
    echo ""
    echo "Check service status:"
    echo "  sudo systemctl status scrapping-flask"
    echo ""
    echo "View logs:"
    echo "  sudo journalctl -u scrapping-flask -f"
else
    echo "✗ Some dependencies are still missing"
    exit 1
fi

