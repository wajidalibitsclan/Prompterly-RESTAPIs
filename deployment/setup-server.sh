#!/bin/bash

# Prompterly Server Setup Script
# Run this on your server: bash setup-server.sh

set -e

PROJECT_PATH="/home/prompterly/public_html"
BACKEND_PATH="$PROJECT_PATH"
FRONTEND_PATH="$PROJECT_PATH/prompterly"

echo "=========================================="
echo "  Prompterly Server Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo bash setup-server.sh)"
    exit 1
fi

# Update system
echo "[1/8] Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "[2/8] Installing required packages..."
apt install -y python3 python3-pip python3-venv nodejs npm apache2 git

# Create project directory if not exists
echo "[3/8] Setting up project directory..."
mkdir -p $PROJECT_PATH
cd $PROJECT_PATH

# Check if git repo exists
if [ ! -d ".git" ]; then
    echo "Please clone your repository to $PROJECT_PATH first!"
    echo "Run: git clone YOUR_REPO_URL $PROJECT_PATH"
    exit 1
fi

# Setup Python virtual environment
echo "[4/8] Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup Frontend
echo "[5/8] Building frontend..."
cd $FRONTEND_PATH
npm install
npm run build
cd $PROJECT_PATH

# Setup systemd service
echo "[6/8] Setting up backend service..."
cp deployment/prompterly-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable prompterly-backend
systemctl start prompterly-backend

# Setup Apache
echo "[7/8] Setting up Apache..."
a2enmod proxy proxy_http rewrite headers || true
cp deployment/prompterly-apache.conf /etc/apache2/sites-available/prompterly.conf
a2ensite prompterly.conf
apache2ctl configtest && systemctl reload apache2

# Create uploads directory
echo "[8/8] Creating uploads directory..."
mkdir -p $PROJECT_PATH/uploads
chmod 755 $PROJECT_PATH/uploads

echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Backend service: prompterly-backend"
echo "  - Status: systemctl status prompterly-backend"
echo "  - Logs: journalctl -u prompterly-backend -f"
echo ""
echo "Frontend: Served via Apache"
echo "  - Path: $FRONTEND_PATH/dist"
echo ""
echo "Don't forget to:"
echo "1. Update the .env file with your configuration"
echo "2. Run database migrations: alembic upgrade head"
echo "=========================================="
