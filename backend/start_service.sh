#!/bin/bash
# start_service.sh
# Start the course updater as a background service

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the service in the background
nohup python3 scheduler.py --service > logs/service.log 2>&1 &

# Save the PID
echo $! > scheduler.pid

echo "✅ Course updater service started (PID: $(cat scheduler.pid))"
echo "   Logs: logs/service.log and logs/scheduler_YYYYMMDD.log"
echo ""
echo "To stop: ./stop_service.sh"
echo "To check status: ps aux | grep scheduler.py"

