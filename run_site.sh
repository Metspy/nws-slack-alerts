#!/bin/bash

SITE=$1
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$BASE_DIR" || exit 1

# Load environment variables
set -a
source .env
set +a

LOGFILE="$BASE_DIR/logs/${SITE}.log"

echo "========== $(date -u) : Running $SITE ==========" >> "$LOGFILE"

# Run script ONCE
if /opt/anaconda3/envs/nws_automation/bin/python nws_alerts.py --config "configs/${SITE}.json" >> "$LOGFILE" 2>&1; then
    date +%s > "$BASE_DIR/logs/${SITE}.last_success"
else
    echo "Script failed at $(date)" >> "$LOGFILE"
fi

echo "" >> "$LOGFILE"

