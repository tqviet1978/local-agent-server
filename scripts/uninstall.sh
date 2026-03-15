#!/bin/bash
# Local Agent Server - Uninstall Script

set -e

echo "================================================"
echo "Local Agent Server - Uninstall"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "⚠️  This will remove:"
echo "   - systemd service"
echo "   - /var/www/local-agent-server/"
echo "   - /var/log/local-agent-server/"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted."
    exit 0
fi

echo ""
echo "🛑 Stopping and disabling service..."
systemctl stop local-agent-server 2>/dev/null && echo "   ✓ Service stopped" || echo "   ℹ️  Service was not running"
systemctl disable local-agent-server 2>/dev/null && echo "   ✓ Service disabled" || echo "   ℹ️  Service was not enabled"

echo ""
echo "🗑️  Removing systemd service file..."
rm -f /etc/systemd/system/local-agent-server.service
systemctl daemon-reload
echo "   ✓ Service file removed"

echo ""
echo "🗑️  Removing installation directory..."
rm -rf /var/www/local-agent-server
echo "   ✓ /var/www/local-agent-server removed"

echo ""
echo "🗑️  Removing log directory..."
rm -rf /var/log/local-agent-server
echo "   ✓ /var/log/local-agent-server removed"

echo ""
echo "✅ Verifying..."
systemctl status local-agent-server 2>&1 | grep -q "could not be found" && echo "   ✓ Service removed" || echo "   ⚠️  Service still exists"
[ ! -d "/var/www/local-agent-server" ] && echo "   ✓ Install dir removed" || echo "   ⚠️  Install dir still exists"
[ ! -d "/var/log/local-agent-server" ] && echo "   ✓ Log dir removed" || echo "   ⚠️  Log dir still exists"

echo ""
echo "================================================"
echo "✅ Uninstall completed!"
echo "================================================"
echo ""
echo "💡 To reinstall, run:"
echo "   sudo bash scripts/setup.sh"
echo ""
