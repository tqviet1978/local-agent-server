#!/bin/bash
# Stop Local Agent Server service

set -e

echo "================================================"
echo "Stopping Local Agent Server"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "🛑 Stopping Local Agent Server..."
systemctl stop local-agent-server

echo ""
echo "================================================"
echo "✅ Service stopped!"
echo "================================================"
echo ""
