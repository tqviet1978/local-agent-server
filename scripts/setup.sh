#!/bin/bash
# Local Agent Server - Setup Script for Debian 12

set -e

echo "================================================"
echo "Local Agent Server - Setup"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/var/www/local-agent-server"

echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-venv python3-pip

echo ""
echo "📁 Creating installation directory..."
mkdir -p $INSTALL_DIR
mkdir -p /var/log/local-agent-server

echo ""
echo "📋 Copying project files (excluding venv)..."
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    $PROJECT_DIR/src/ $INSTALL_DIR/src/

echo ""
echo "🐍 Setting up Python virtual environment..."
cd $INSTALL_DIR/src
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install gunicorn          # required to run as a service
venv/bin/pip install -r requirements.txt

echo ""
echo "🔧 Setting up systemd service..."
cp $SCRIPT_DIR/local-agent-server.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "👤 Setting permissions..."
chown -R www-data:www-data $INSTALL_DIR
chown -R www-data:www-data /var/log/local-agent-server

echo ""
echo "================================================"
echo "✅ Setup completed!"
echo "================================================"
echo ""
echo "⚠️  IMPORTANT: Next steps:"
echo ""
echo "1. Edit config.json:"
echo "   nano $INSTALL_DIR/src/config.json"
echo "   - Change auth_token"
echo "   - Add your repositories"
echo ""
echo "2. Start the service:"
echo "   sudo scripts/start.sh"
echo ""
echo "3. Expose to internet (in another terminal):"
echo "   ngrok http 5000"
echo ""
