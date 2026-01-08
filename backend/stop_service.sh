#!/bin/bash
# stop_service.sh
# Stop the course updater service

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -f scheduler.pid ]; then
    PID=$(cat scheduler.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm scheduler.pid
        echo "✅ Service stopped (PID: $PID)"
    else
        echo "⚠️  Service not running (PID file exists but process not found)"
        rm scheduler.pid
    fi
else
    echo "⚠️  No PID file found. Service may not be running."
    echo "   Trying to find and kill any running scheduler processes..."
    pkill -f "scheduler.py --service"
    echo "   Done."
fi

