#!/usr/bin/env python3
"""Automated daily fight runner - ensures we never waste fights.

Designed for cron/GitHub Actions to guarantee daily fight usage.

Usage:
    # Run all remaining fights (23:30 fallback)
    poetry run python scripts/auto_daily_fights.py

    # Run 25% of remaining (for progressive scheduling)
    poetry run python scripts/auto_daily_fights.py --percent 25

    # Run if more than N fights remaining
    poetry run python scripts/auto_daily_fights.py --min-remaining 50

    # Dry run (check status only)
    poetry run python scripts/auto_daily_fights.py --dry-run

Cron examples:
    # 23:30 - use all remaining (last chance)
    30 23 * * * cd /path/to/project && poetry run python scripts/auto_daily_fights.py >> logs/auto_fights.log 2>&1

    # Progressive: 8pm=25%, 9pm=25%, 10pm=25%, 11pm=100%
    0 20 * * * cd /path && poetry run python scripts/auto_daily_fights.py --percent 25
    0 21 * * * cd /path && poetry run python scripts/auto_daily_fights.py --percent 25
    0 22 * * * cd /path && poetry run python scripts/auto_daily_fights.py --percent 25
    30 23 * * * cd /path && poetry run python scripts/auto_daily_fights.py  # fallback: all remaining
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api

# Config
LEEK_ID = 131321
LOG_FILE = Path(__file__).parent.parent / "logs" / "auto_fights.log"


def log(msg: str, also_print: bool = True):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    if also_print:
        print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def get_status(api: LeekWarsAPI) -> dict:
    """Get current fight status."""
    garden = api.get_garden()["garden"]
    farmer = api.farmer
    leek = list(farmer["leeks"].values())[0]

    return {
        "fights_available": garden.get("fights", 0),
        "fights_max": garden.get("max_fights", 150),
        "leek_name": leek.get("name", "Unknown"),
        "leek_level": leek.get("level", 0),
        "talent": leek.get("talent", 0),
    }


def run_fights(api: LeekWarsAPI, count: int) -> dict:
    """Run N fights and return results."""

    leek_id = LEEK_ID
    wins, losses, draws, crashes = 0, 0, 0, 0

    for i in range(count):
        try:
            opponents = api.get_leek_opponents(leek_id).get("opponents", [])
            if not opponents:
                log(f"  [{i+1}/{count}] No opponents available")
                break

            target = opponents[0]
            result = api.start_fight(leek_id, target["id"])

            if "fight" not in result:
                log(f"  [{i+1}/{count}] Fight failed: {result}")
                crashes += 1
                continue

            fight_id = result["fight"]
            import time
            time.sleep(3)  # Wait for fight to complete

            fight_data = api.get_fight(fight_id)
            fight = fight_data.get("fight", {})
            winner = fight.get("winner", 0)
            my_team = 1  # We're always team 1 when attacking

            if winner == my_team:
                wins += 1
                result_char = "W"
            elif winner == 0:
                draws += 1
                result_char = "D"
            else:
                losses += 1
                result_char = "L"

            # Check for crash
            report = fight.get("report", {})
            if report.get("flags", 0) & 1:  # Crash flag
                crashes += 1
                result_char += " [CRASH]"

            opponent_name = target.get("name", "Unknown")
            log(f"  [{i+1}/{count}] {result_char} vs {opponent_name}")

            time.sleep(0.5)  # Rate limit

        except Exception as e:
            log(f"  [{i+1}/{count}] Error: {e}")
            crashes += 1

    return {
        "fights_run": wins + losses + draws,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "crashes": crashes,
        "win_rate": wins / (wins + losses) * 100 if (wins + losses) > 0 else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Automated daily fight runner")
    parser.add_argument("--percent", type=int, default=100,
                        help="Percentage of remaining fights to use (default: 100)")
    parser.add_argument("--min-remaining", type=int, default=0,
                        help="Only run if at least N fights remaining")
    parser.add_argument("--max-fights", type=int, default=0,
                        help="Maximum fights to run (0 = no limit)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check status only, don't fight")
    args = parser.parse_args()

    log("=" * 50)
    log("AUTO DAILY FIGHTS - Starting")

    # Login via centralized auth (reads LEEKWARS_USER/LEEKWARS_PASS env vars)
    try:
        api = login_api()
        log(f"Logged in as {api.farmer['name']}")
    except Exception as e:
        log(f"LOGIN FAILED: {e}")
        sys.exit(1)

    # Get status
    status = get_status(api)
    log(f"Status: {status['fights_available']}/{status['fights_max']} fights | "
        f"L{status['leek_level']} {status['leek_name']} | Talent: {status['talent']}")

    available = status["fights_available"]

    # Check minimum threshold
    if available < args.min_remaining:
        log(f"Only {available} fights remaining (min: {args.min_remaining}), skipping")
        api.close()
        return

    # Calculate fights to run
    to_run = int(available * args.percent / 100)
    if args.max_fights > 0:
        to_run = min(to_run, args.max_fights)
    to_run = max(1, to_run) if available > 0 else 0

    if to_run == 0:
        log("No fights to run")
        api.close()
        return

    log(f"Plan: Run {to_run} fights ({args.percent}% of {available})")

    if args.dry_run:
        log("DRY RUN - Would run but not executing")
        api.close()
        return

    # Run fights
    results = run_fights(api, to_run)
    log(f"Results: {results['wins']}W-{results['losses']}L-{results['draws']}D "
        f"({results['win_rate']:.1f}% WR) | {results['crashes']} crashes")

    # Final status
    final_status = get_status(api)
    log(f"Final: {final_status['fights_available']} fights remaining | "
        f"L{final_status['leek_level']} | Talent: {final_status['talent']}")

    api.close()
    log("AUTO DAILY FIGHTS - Complete")
    log("=" * 50)


if __name__ == "__main__":
    main()
