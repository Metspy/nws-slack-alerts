#!/bin/bash
set -euo pipefail

SITE=$1
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$BASE_DIR" || exit 1

# Load environment variables
set -a
source .env
set +a

LOGFILE="$BASE_DIR/logs/${SITE}.log"

echo "========== $(date -u) : Running $SITE ==========" >> "$LOGFILE"

"$BASE_DIR/venv/bin/python" nws_alerts.py --config "configs/${SITE}.json" >> "$LOGFILE" 2>&1
rc=$?

if [ $rc -eq 0 ]; then
    echo "$(date -u) python exit OK" >> "$LOGFILE"
else
    echo "$(date -u) python exit code $rc" >> "$LOGFILE"
fi

date +%s > "$BASE_DIR/logs/${SITE}.last_success"
