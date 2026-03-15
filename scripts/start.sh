#!/bin/bash
# Start Local Agent Server service

set -e

echo "================================================"
echo "Starting Local Agent Server"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "🚀 Starting Local Agent Server..."
systemctl start local-agent-server
systemctl enable local-agent-server

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
echo "✅ Service started!"
echo "================================================"
echo ""
echo "🌐 Server is listening on: http://127.0.0.1:5000"
echo ""
echo "📊 To check logs:"
echo "   sudo scripts/logs.sh"
echo "   journalctl -u local-agent-server -f"
echo ""
echo "💡 Remember to expose via ngrok if needed:"
echo "   ngrok http 5000"
echo ""
