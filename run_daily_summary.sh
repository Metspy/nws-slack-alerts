#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
set -a
source .env
set +a

echo "========== $(date -u) : Running Daily Summary ==========" >> logs/daily_summary.log

# Run summary script
./venv/bin/python tools/daily_alert_summary.py >> logs/daily_summary.log 2>&1
