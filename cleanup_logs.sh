#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$BASE_DIR/logs"

# Keep last 7 days of logs
find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete

# Also trim huge logs (keep last 2000 lines)
for file in "$LOG_DIR"/*.log; do
    [ -f "$file" ] || continue
    tail -n 2000 "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done

