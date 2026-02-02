#!/bin/bash
#
# Pigeon Poller Runner Script
#
# This script manages the pigeon-poller process in the background.
# It uses a PID file for process tracking and logs all output to a dedicated log file.
#
# Usage:
#   ./scripts/run-poller.sh status    # Check poller status
#   ./scripts/run-poller.sh start     # Start poller in background
#   ./scripts/run-poller.sh stop      # Stop the running poller
#   ./scripts/run-poller.sh restart   # Restart the poller
#   ./scripts/run-poller.sh help      # Show this help
#

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/tmp/pigeon-poller.pid"
LOG_FILE="$PROJECT_ROOT/tmp/pigeon-poller.log"

# Configuration for venv
VENV_BIN="$PROJECT_ROOT/venv/bin"
PYTHON_BIN="$VENV_BIN/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Create tmp directory if it doesn't exist
mkdir -p tmp

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*" >&2
}

error() {
    echo -e "${RED}ERROR:${NC} $*" >&2
}

success() {
    echo -e "${GREEN}SUCCESS:${NC} $*" >&2
}

warning() {
    echo -e "${YELLOW}WARNING:${NC} $*" >&2
}

# Check if process is running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Running
        else
            # Stale PID file
            rm -f "$PID_FILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Get process info
get_process_info() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "PID: $pid"
            echo "Command: $(ps -p "$pid" -o comm=)"
            echo "Started: $(ps -p "$pid" -o lstart=)"
            echo "Log file: $LOG_FILE"
            return 0
        fi
    fi
    echo "Poller is not running"
    return 1
}

# Status command
cmd_status() {
    log "Checking poller status..."
    if is_running; then
        success "Poller is running"
        get_process_info
        echo ""
        echo "To view recent logs (last 20 lines):"
        echo "  tail -n 20 $LOG_FILE"
        echo ""
        echo "To follow logs in real-time:"
        echo "  tail -f $LOG_FILE"
    else
        warning "Poller is not running"
        echo "Log file: $LOG_FILE"
        echo ""
        echo "To check recent logs (if any exist):"
        echo "  tail -n 20 $LOG_FILE"
    fi
}

# Start command
cmd_start() {
    log "Starting poller..."

    if is_running; then
        error "Poller is already running"
        get_process_info
        exit 1
    fi

    # Check if venv exists
    if [[ ! -f "$PYTHON_BIN" ]]; then
        error "Virtual environment not found at $PROJECT_ROOT/venv"
        exit 1
    fi

    log "Launching poller in background..."
    log "All output will be logged to: $LOG_FILE"

    nohup env PYTHONPATH="$PROJECT_ROOT" "$PYTHON_BIN" -m pigeon.main start >> "$LOG_FILE" 2>&1 &
    local pid=$!

    sleep 2

    if ! kill -0 "$pid" 2>/dev/null; then
        error "Poller failed to start (process exited immediately)"
        echo "Check the log file for errors:"
        echo "  tail -n 50 $LOG_FILE"
        exit 1
    fi

    echo $pid > "$PID_FILE"
    success "Poller started successfully"
    echo "PID: $pid"
    echo "Log file: $LOG_FILE"
}

# Stop command
cmd_stop() {
    log "Stopping poller..."

    if ! is_running; then
        warning "Poller is not running"
        return 0
    fi

    local pid=$(cat "$PID_FILE" 2>/dev/null)
    if [[ -z "$pid" ]]; then
        error "Failed to read PID from $PID_FILE"
        return 1
    fi

    log "Sending SIGTERM to process $pid..."
    kill -TERM "$pid" 2>/dev/null || true

    local count=0
    while kill -0 "$pid" 2>/dev/null && [[ $count -lt 30 ]]; do
        sleep 1
        ((count++)) || true
    done || true

    if kill -0 "$pid" 2>/dev/null; then
        log "Poller didn't respond to SIGTERM, sending SIGKILL..."
        kill -KILL "$pid" 2>/dev/null || true

        local sigkill_count=0
        while kill -0 "$pid" 2>/dev/null && [[ $sigkill_count -lt 5 ]]; do
            sleep 1
            ((sigkill_count++))
        done
    fi

    rm -f "$PID_FILE"
    success "Poller stopped"
    echo "Log file remains at: $LOG_FILE"
}

# Restart command
cmd_restart() {
    log "Restarting poller..."
    cmd_stop
    sleep 2
    log "Starting poller..."
    cmd_start
}

# Help command
cmd_help() {
    cat << EOF
Pigeon Poller Runner Script

USAGE:
    $0 <command>

COMMANDS:
    status    Check if poller is running and show process info
    start     Start the poller in background
    stop      Stop the running poller gracefully
    restart   Restart the poller (stop then start)
    help      Show this help message

FILES:
    PID file: $PID_FILE
    Log file: $LOG_FILE

EXAMPLES:
    $0 status
    $0 start
    $0 stop
    $0 restart

LOGGING:
    All poller output is appended to: $LOG_FILE
    View recent logs: tail -n 20 $LOG_FILE
    Follow logs: tail -f $LOG_FILE

NOTES:
    - Poller must be run from the project root directory
    - Make sure virtual environment is set up
    - Log file will grow over time; consider log rotation
EOF
}

# Main command dispatcher
case "${1:-help}" in
    status)
        cmd_status
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        error "Unknown command: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
