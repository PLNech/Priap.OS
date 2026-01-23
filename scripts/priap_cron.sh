#!/bin/bash
# Priap.OS - Automated Daily Fight Runner
# Install: crontab -e, then add the line at the bottom of this file
#
# This script:
# 1. Loads environment variables (for LEEKWARS_USER/LEEKWARS_PASS)
# 2. Buys 50-fight pack if not done today (for 150/day capacity)
# 3. Runs all remaining fights
#
# Recommended schedule: Run at 23:30 local time (before daily reset)

PROJECT_DIR="/home/pln/Work/Perso/Priap.OS"
POETRY="/home/pln/.local/bin/poetry"
LOG_FILE="$PROJECT_DIR/logs/auto_fights.log"

# Load environment (credentials stored in .env)
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Run the auto-fight script
cd "$PROJECT_DIR"
$POETRY run python scripts/auto_daily_fights.py >> "$LOG_FILE" 2>&1

# ============================================================================
# CRONTAB ENTRY (add this to your crontab with: crontab -e)
# ============================================================================
# Run at 23:30 every day (just before midnight reset)
# 30 23 * * * /home/pln/Work/Perso/Priap.OS/scripts/priap_cron.sh
#
# Optional: Progressive schedule to spread fights throughout the evening
# 0 20 * * * /home/pln/Work/Perso/Priap.OS/scripts/priap_cron.sh --percent 25
# 0 21 * * * /home/pln/Work/Perso/Priap.OS/scripts/priap_cron.sh --percent 25
# 0 22 * * * /home/pln/Work/Perso/Priap.OS/scripts/priap_cron.sh --percent 25
# 30 23 * * * /home/pln/Work/Perso/Priap.OS/scripts/priap_cron.sh  # fallback
