#!/bin/bash
# Deploy latest code to Local Agent Server

set -e

echo "================================================"
echo "Local Agent Server - Deploy Update"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/var/www/local-agent-server"

echo "📋 Copying updated source files (excluding venv)..."
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    $PROJECT_DIR/src/ $INSTALL_DIR/src/

echo ""
echo "📋 Copying install.sh (if exists)..."
if [ -f "$PROJECT_DIR/scripts/install.sh" ]; then
    mkdir -p $INSTALL_DIR/scripts
    cp $PROJECT_DIR/scripts/install.sh $INSTALL_DIR/scripts/
    echo "   ✓ install.sh copied to $INSTALL_DIR/scripts/"
else
    echo "   ℹ️  install.sh not found, skipping (run: bash scripts/bundle.sh)"
fi

echo ""
echo "📥 Updating dependencies..."
$INSTALL_DIR/src/venv/bin/pip install -r $INSTALL_DIR/src/requirements.txt -q

echo ""
echo "👤 Fixing permissions..."
chown -R www-data:www-data $INSTALL_DIR

echo ""
echo "🔄 Restarting service..."
systemctl restart local-agent-server

echo ""
echo "✅ Checking service status..."
echo ""

if systemctl is-active --quiet local-agent-server; then
    echo "✅ Local Agent Server: Running"
else
    echo "❌ Local Agent Server: Failed after deploy"
    systemctl status local-agent-server --no-pager
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Deploy completed!"
echo "================================================"
echo ""