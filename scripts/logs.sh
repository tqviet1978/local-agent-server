#!/bin/bash
# View Local Agent Server logs

echo "================================================"
echo "Local Agent Server - Logs"
echo "================================================"
echo ""
echo "1. Service logs (systemd)"
echo "2. Application access log"
echo "3. Application error log"
echo "4. Follow all logs (tail -f)"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📊 Service logs (systemd):"
        echo "Press Ctrl+C to exit"
        echo ""
        journalctl -u local-agent-server -f
        ;;
    2)
        echo ""
        echo "📊 Application access log:"
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f /var/log/local-agent-server/access.log
        ;;
    3)
        echo ""
        echo "📊 Application error log:"
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f /var/log/local-agent-server/error.log
        ;;
    4)
        echo ""
        echo "📊 All logs:"
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f /var/log/local-agent-server/access.log \
                /var/log/local-agent-server/error.log
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac
