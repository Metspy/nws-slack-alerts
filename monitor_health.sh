#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR" || exit 1

set -a
source .env
set +a

send_slack () {
    local TEXT="$1"

    if [ -z "$OPS_SLACK_WEBHOOK" ]; then
        echo "MONITOR ERROR: OPS_SLACK_WEBHOOK not set"
        return
    fi

    curl -s -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$TEXT\"}" \
        "$OPS_SLACK_WEBHOOK" >/dev/null 2>&1

    if [ $? -ne 0 ]; then
        echo "MONITOR: Failed to send Slack message: $TEXT"
    fi
}

SITES=("DST" "BNF" "SGP")
MAX_AGE=600   # seconds (10 minutes)

for SITE in "${SITES[@]}"; do

    LAST_FILE="logs/${SITE}.last_success"
    STATE_FILE="logs/${SITE}.state"

    CURRENT_STATE="OK"
    MESSAGE=""

    if [ ! -f "$LAST_FILE" ]; then
        CURRENT_STATE="FAIL"
        MESSAGE="⚠️ $SITE weather alert script has never succeeded"
    else
        RAW_LAST=$(cat "$LAST_FILE")

        if [[ "$RAW_LAST" =~ ^[0-9]+$ ]]; then
            LAST_RUN=$RAW_LAST
        else
            LAST_RUN=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${RAW_LAST%%.*}" "+%s" 2>/dev/null)
        fi

        NOW=$(date +%s)
        AGE=$((NOW - LAST_RUN))

        if [ $AGE -gt $MAX_AGE ]; then
            CURRENT_STATE="FAIL"
            MESSAGE="🚨 $SITE weather alert script stalled — last success ${AGE}s ago"
        fi
    fi

    PREVIOUS_STATE="OK"
    [ -f "$STATE_FILE" ] && PREVIOUS_STATE=$(cat "$STATE_FILE")

    # ---------- STATE TRANSITIONS ----------
    if [[ "$CURRENT_STATE" == "FAIL" && "$PREVIOUS_STATE" == "OK" ]]; then
        echo "MONITOR: $SITE entered FAIL state: $MESSAGE"
        send_slack "$MESSAGE"

    elif [[ "$CURRENT_STATE" == "OK" && "$PREVIOUS_STATE" == "FAIL" ]]; then
        echo "MONITOR: $SITE recovered"
        send_slack "✅ $SITE weather alert script recovered"
    fi

    echo "$CURRENT_STATE" > "$STATE_FILE"

done

