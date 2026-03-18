#!/bin/bash
# Priap.OS - Daily Ranking Snapshot
# Safe for laptops: runs at most once per calendar day regardless of uptime.
# Cron: run every hour so any window the machine is on gets caught.
#
#   0 * * * * /home/pln/Work/Perso/Priap.OS/scripts/ranking_daily.sh >> logs/ranking.log 2>&1

PROJECT_DIR="/home/pln/Work/Perso/Priap.OS"
POETRY="/home/pln/.local/bin/poetry"
STATE_FILE="$PROJECT_DIR/logs/.ranking_last_run"
TODAY=$(date +%Y-%m-%d)

# Load credentials
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Exit if already ran successfully today
if [ -f "$STATE_FILE" ] && [ "$(cat $STATE_FILE)" = "$TODAY" ]; then
    exit 0
fi

echo "=== Ranking snapshot: $TODAY $(date +%H:%M) ==="
cd "$PROJECT_DIR" || exit 1

# Quick rank check (1 API call)
$POETRY run python scripts/ranking_tracker.py --quick || { echo "ERROR: quick rank failed"; exit 1; }

# Full top-10K snapshot
$POETRY run python scripts/ranking_tracker.py --pages 200 || { echo "ERROR: full snapshot failed"; exit 1; }

# Export to site JSON
$POETRY run python scripts/export_rankings.py || { echo "ERROR: export failed"; exit 1; }

# Mark success
echo "$TODAY" > "$STATE_FILE"
echo "=== Done ==="
