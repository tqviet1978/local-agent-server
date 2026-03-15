#!/bin/bash
# Restart Local Agent Server service

set -e

echo "================================================"
echo "Restarting Local Agent Server"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "🔄 Restarting Local Agent Server..."
systemctl restart local-agent-server

echo ""
echo "✅ Checking service status..."
echo ""

if systemctl is-active --quiet local-agent-server; then
    echo "✅ Local Agent Server: Running"
else
    echo "❌ Local Agent Server: Failed"
    systemctl status local-agent-server --no-pager
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Service restarted!"
echo "================================================"
echo ""
