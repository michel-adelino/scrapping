#!/bin/bash
# Quick fix for Chrome dependencies on Ubuntu 24.04+

echo "Installing Chrome dependencies for Ubuntu 24.04+..."

sudo apt install -y \
    libnss3 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1

# Install Ubuntu 24.04+ specific packages
sudo apt install -y libatk-bridge2.0-0t64 libasound2t64

echo "Chrome dependencies installed successfully!"

