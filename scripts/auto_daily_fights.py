#!/usr/bin/env python3
"""Automated daily fight runner - ensures we never waste fights.

Designed for cron/GitHub Actions to guarantee daily fight usage.
AUTOMATICALLY BUYS 50-fight packs to maximize daily capacity (150/day).

Usage:
    # Run all remaining fights (23:30 fallback)
    poetry run python scripts/auto_daily_fights.py

    # Run 25% of remaining (for progressive scheduling)
    poetry run python scripts/auto_daily_fights.py --percent 25

    # Run if more than N fights remaining
    poetry run python scripts/auto_daily_fights.py --min-remaining 50

    # Skip buying fights (just run what we have)
    poetry run python scripts/auto_daily_fights.py --no-buy

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
from datetime import datetime, date
from pathlib import Path

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api
from leekwars_agent.db import store_fight, init_db
from leekwars_agent.fight_parser import parse_fight
from leekwars_agent.fight_analyzer import classify_ai_behavior
from leekwars_agent.models.fight import ActionCode
from leekwars_agent.cli.constants import LEEKS, LEEK_ID, resolve_leek

# Config
LOG_FILE = Path(__file__).parent.parent / "logs" / "auto_fights.log"
STATE_FILE = Path(__file__).parent.parent / "data" / "daily_state.json"


def log(msg: str, also_print: bool = True):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    if also_print:
        print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_state() -> dict:
    """Load daily state from file."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    """Save daily state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def buy_fight_pack(api: LeekWarsAPI, state: dict) -> bool:
    """Buy 50-fight pack if not done today and affordable.

    Returns True if pack was bought or already done, False if failed.
    """
    task = "buy_fights"
    today = date.today().isoformat()

    # Check if already done today
    last_run = state.get(task, {}).get("last_date")
    if last_run == today:
        log(f"[{task}] Already purchased today, skipping")
        return True

    def mark(result: str):
        state[task] = {
            "last_date": today,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        save_state(state)

    def describe_http_error(exc: httpx.HTTPStatusError) -> tuple[str, dict | None]:
        status = exc.response.status_code if exc.response is not None else "?"
        body = exc.response.text if exc.response is not None else ""
        if len(body) > 300:
            body = body[:300] + "...[truncated]"
        data = None
        if exc.response is not None:
            try:
                parsed = exc.response.json()
                if isinstance(parsed, dict):
                    data = parsed
            except Exception:
                pass
        return f"status={status} body={body or '<empty>'}", data

    try:
        result = api.buy_fights(quantity=1)
        log(f"[{task}] Bought 50-fight pack! Result: {result}")
        mark("success")
        return True
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        desc, payload = describe_http_error(e)
        if status == 401 and payload and payload.get("error") == "not_enough_habs":
            log(f"[{task}] Not enough habs (price={payload.get('price')}); will retry later")
            return False
        if status == 401:
            log(f"[{task}] Unauthorized response ({desc}), skipping purchase")
            return False
        if status == 402:
            log(f"[{task}] Not enough habs to buy pack (will retry later)")
            return False
        if status == 400:
            log(f"[{task}] Already at max fights or limit reached")
            mark("limit_reached")
            return True
        log(f"[{task}] Error buying pack: {desc}")
        return False
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "not enough" in error_msg.lower():
            log(f"[{task}] Not enough habs to buy pack (will retry later)")
            return False
        if "400" in error_msg:
            log(f"[{task}] Already at max fights or limit reached")
            mark("limit_reached")
            return True
        log(f"[{task}] Error buying pack: {e}")
        return False


def get_status(api: LeekWarsAPI, leek_id: int = LEEK_ID) -> dict:
    """Get current fight status for a specific leek."""
    garden = api.get_garden()["garden"]
    leek_data = api.get_leek(leek_id)
    leek = leek_data.get("leek", leek_data)

    return {
        "fights_available": garden.get("fights", 0),
        "fights_max": garden.get("max_fights", 150),
        "leek_name": leek.get("name", "Unknown"),
        "leek_level": leek.get("level", 0),
        "talent": leek.get("talent", 0),
    }


def run_fights(api: LeekWarsAPI, count: int, leek_id: int = LEEK_ID) -> dict:
    """Run N fights for a specific leek and return results."""
    from collections import defaultdict

    wins, losses, draws, crashes = 0, 0, 0, 0
    archetype_stats = defaultdict(lambda: {"W": 0, "L": 0, "D": 0})

    for i in range(count):
        try:
            opponents = api.get_leek_opponents(leek_id).get("opponents", [])
            if not opponents:
                log(f"  [{i+1}/{count}] No opponents available")
                break

            target = opponents[0]
            result = api.start_solo_fight(leek_id, target["id"])

            if "fight" not in result:
                log(f"  [{i+1}/{count}] Fight failed: {result}")
                crashes += 1
                continue

            fight_id = result["fight"]
            import time
            time.sleep(3)  # Wait for fight to complete

            fight_data = api.get_fight(fight_id)
            fight = fight_data.get("fight", fight_data)

            # Store fight in database for analysis
            try:
                # Ensure fight has ID (sometimes nested differently)
                if "id" not in fight:
                    fight["id"] = fight_id
                store_fight(fight)
            except Exception as db_err:
                log(f"  [{i+1}/{count}] DB save failed: {db_err}")

            winner = fight.get("winner", 0)

            # Helper: extract leek ID from various formats (dict or int)
            def get_leek_id(leek):
                if isinstance(leek, dict):
                    return leek.get("id")
                elif isinstance(leek, int):
                    return leek
                return None

            # Determine which team we're on (don't assume team 1!)
            my_team = None
            leeks1 = fight.get("leeks1", [])
            leeks2 = fight.get("leeks2", [])

            for leek in leeks1:
                if get_leek_id(leek) == leek_id:
                    my_team = 1
                    break
            if my_team is None:
                for leek in leeks2:
                    if get_leek_id(leek) == leek_id:
                        my_team = 2
                        break

            # Handle cancelled fights (winner=-1) or unknown team
            if winner == -1 or my_team is None:
                if winner == -1:
                    result_char = "C"  # Cancelled
                    crashes += 1  # Count as non-result
                elif my_team is None:
                    my_team = 1
                    result_char = "?"
                    log(f"  [{i+1}/{count}] WARNING: Couldn't determine team, assuming 1")
                continue  # Skip DB update for cancelled/unknown fights

            if winner == 0:
                draws += 1
                result_char = "D"  # Actual draw (turn 64 timeout)
            elif winner == my_team:
                wins += 1
                result_char = "W"
            else:
                losses += 1
                result_char = "L"

            # Check for crash
            report = fight.get("report", {})
            if report.get("flags", 0) & 1:  # Crash flag
                crashes += 1
                result_char += " [CRASH]"

            # Extract useful stats for logging
            opponent_name = target.get("name", "Unknown")
            # Actions is a flat list; count NEW_TURN entries for turn count
            actions_list = fight.get("data", {}).get("actions", [])
            turn_count = sum(1 for a in actions_list if a[0] == ActionCode.NEW_TURN) if actions_list else "?"

            # Get final HP if available
            my_hp = "?"
            enemy_hp = "?"
            if fight.get("data", {}).get("leeks"):
                for ldata in fight["data"]["leeks"]:
                    if ldata.get("id") == leek_id:
                        my_hp = ldata.get("life", "?")
                    elif ldata.get("team") != my_team:
                        enemy_hp = ldata.get("life", "?")

            # Classify opponent archetype
            opp_archetype = "?"
            try:
                parsed = parse_fight(fight)
                data = fight.get("data", {})
                for leek in data.get("leeks", []):
                    if leek.get("team") != my_team:
                        opp_entity_id = leek.get("id")
                        classification = classify_ai_behavior(parsed, opp_entity_id)
                        opp_archetype = classification.archetype
                        break
            except Exception:
                pass  # Classification is optional, don't fail fight

            log(f"  [{i+1}/{count}] {result_char} vs {opponent_name} [{opp_archetype}] (t{turn_count}, HP:{my_hp}/{enemy_hp})")

            # Track per-archetype stats
            if opp_archetype != "?":
                if winner == 0:
                    archetype_stats[opp_archetype]["D"] += 1
                elif winner == my_team:
                    archetype_stats[opp_archetype]["W"] += 1
                else:
                    archetype_stats[opp_archetype]["L"] += 1

            time.sleep(0.5)  # Rate limit

        except Exception as e:
            log(f"  [{i+1}/{count}] Error: {e}")
            crashes += 1

    # Log archetype breakdown
    if archetype_stats:
        log("  Archetype breakdown:")
        for arch, stats in sorted(archetype_stats.items()):
            total = stats["W"] + stats["L"] + stats["D"]
            wr = stats["W"] / (stats["W"] + stats["L"]) * 100 if (stats["W"] + stats["L"]) > 0 else 0
            log(f"    vs {arch}: {stats['W']}W-{stats['L']}L-{stats['D']}D ({wr:.0f}% WR)")

    return {
        "fights_run": wins + losses + draws,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "crashes": crashes,
        "win_rate": wins / (wins + losses) * 100 if (wins + losses) > 0 else 0,
        "archetype_stats": dict(archetype_stats),
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
    parser.add_argument("--no-buy", action="store_true",
                        help="Skip buying fight packs (just use available)")
    parser.add_argument("--buy-only", action="store_true",
                        help="Attempt to buy fights then exit (debugging)")
    parser.add_argument("--leek", type=str, default=None,
                        help="Leek name or ID (default: IAdonis)")
    parser.add_argument("--all", action="store_true", dest="all_leeks",
                        help="Run fights for ALL registered leeks sequentially")
    args = parser.parse_args()

    # Resolve leek target(s)
    if args.all_leeks:
        leek_ids = list(LEEKS.values())
    elif args.leek:
        leek_ids = [resolve_leek(args.leek)]
    else:
        leek_ids = [LEEK_ID]

    log("=" * 50)
    leek_names = [name for name, lid in LEEKS.items() if lid in leek_ids]
    log(f"AUTO DAILY FIGHTS - Starting ({', '.join(leek_names)})")

    # Initialize fight database
    init_db()

    # Login via centralized auth (reads LEEKWARS_USER/LEEKWARS_PASS env vars)
    try:
        api = login_api()
        log(f"Logged in as {api.farmer['name']}")
    except Exception as e:
        log(f"LOGIN FAILED: {e}")
        sys.exit(1)

    # Buy fight pack if needed (ensures 150/day capacity) — account-wide, once
    if not args.no_buy and not args.dry_run:
        state = load_state()
        buy_fight_pack(api, state)

    if args.buy_only:
        log("[buy_only] Skipping fight scheduling after purchase attempt")
        api.close()
        return

    # Run fights for each leek
    for leek_id in leek_ids:
        leek_data = api.get_leek(leek_id)
        li = leek_data.get("leek", leek_data)
        ai = li.get("ai", {})
        ai_name = ai.get("name", "unknown") if isinstance(ai, dict) else f"ai_{ai}"
        log(f"\n--- {li.get('name', '?')} (#{leek_id}) | AI: {ai_name} ---")

        # Get status
        status = get_status(api, leek_id)
        log(f"Status: {status['fights_available']}/{status['fights_max']} fights | "
            f"L{status['leek_level']} {status['leek_name']} | Talent: {status['talent']}")

        available = status["fights_available"]

        # Check minimum threshold
        if available < args.min_remaining:
            log(f"Only {available} fights remaining (min: {args.min_remaining}), skipping")
            continue

        # Calculate fights to run — split evenly across leeks
        per_leek_available = available // len(leek_ids)
        to_run = int(per_leek_available * args.percent / 100)
        if args.max_fights > 0:
            to_run = min(to_run, args.max_fights)
        to_run = max(1, to_run) if per_leek_available > 0 else 0

        if to_run == 0:
            log("No fights to run for this leek")
            continue

        log(f"Plan: Run {to_run} fights ({args.percent}% of {per_leek_available})")

        if args.dry_run:
            log("DRY RUN - Would run but not executing")
            continue

        # Run fights
        results = run_fights(api, to_run, leek_id)
        log(f"Results: {results['wins']}W-{results['losses']}L-{results['draws']}D "
            f"({results['win_rate']:.1f}% WR) | {results['crashes']} crashes")

        # Scrape recent fights to meta DB for analytics
        try:
            from leekwars_agent.scraper.scraper import FightScraper
            import sqlite3

            log("Scraping recent fights to meta DB...")

            # Get recent fight IDs from leek history
            history = api.get_leek_history(leek_id)
            recent_fights = [f['id'] for f in history.get('fights', [])[:to_run + 10]]

            # Check which are missing from meta DB
            meta_db = sqlite3.connect('data/fights_meta.db')
            existing = set(r[0] for r in meta_db.execute('SELECT fight_id FROM fights').fetchall())
            missing = [fid for fid in recent_fights if fid not in existing]

            if missing:
                scraper = FightScraper(api)
                scraped = 0
                for fid in missing[:50]:  # Limit to avoid rate limits
                    if scraper.process_fight(fid):
                        scraped += 1
                log(f"  Scraped {scraped}/{len(missing)} fights to meta DB")
            else:
                log("  All recent fights already in meta DB")
        except Exception as e:
            log(f"  Scraping failed (non-fatal): {e}")

    # Final status (account-wide)
    final_status = get_status(api, leek_ids[0])
    log(f"\nFinal: {final_status['fights_available']} fights remaining")

    api.close()
    log("AUTO DAILY FIGHTS - Complete")
    log("=" * 50)


if __name__ == "__main__":
    main()
