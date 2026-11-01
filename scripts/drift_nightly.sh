#!/bin/bash
# Nightly drift job: snapshot the stack, check for the new drift, alert via ntfy
set -u

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
LOG_FILE="$PROJECT_DIR/nightly.log"
ENV_FILE="$PROJECT_DIR/.env"

# Read one value from .env, without the spaces & quotes around it
env_value() {
    grep "^$1 *=" "$ENV_FILE" | cut -d= -f2- | tr -d ' "'
}

NTFY_URL="$(env_value NTFY_URL)"
NTFY_KEY="$(env_value NTFY_API_KEY)"

# Push a ntfy notification. $1 = title, $2 = message
send_alert() {
    curl -s --fail -o /dev/null \
        -H "Authorization: Bearer $NTFY_KEY" \
        -H "Title: $1" \
        -d "$2" \
        "${NTFY_URL%/}/$NTFY_TOPIC" || echo "ntfy send failed" >> "$LOG_FILE"
}

cd "$PROJECT_DIR" || exit 1

# 1. Snapshot
echo "=== $(date '+%Y-%m-%d %H:%M:%S') snapshot ===" >> "$LOG_FILE"
"$PYTHON" -m drift.cli snapshot >> "$LOG_FILE" 2>&1
status=$?
if (( status != 0 )); then
    echo "FAILED (exit $status)" >> "$LOG_FILE"
    send_alert "Drift job failed" "snapshot exited $status, see $LOG_FILE"
    exit "$status"
fi

# 2. Check: 0 = clean, 3 = drift found, anything else = crashed
findings=$("$PYTHON" -m drift.cli check 2>&1)
status=$?
echo "$findings" >> "$LOG_FILE"
if (( status == 0 )); then
    echo "ok" >> "$LOG_FILE"
elif (( status == 3 )); then
    send_alert "Stack drift found" "$findings"
    echo "alert sent" >> "$LOG_FILE"
else
    echo "FAILED (exit $status)" >> "$LOG_FILE"
    send_alert "Drift job failed" "check exited $status, see $LOG_FILE"
    exit "$status"
fi
