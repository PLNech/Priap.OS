#!/usr/bin/env python3
"""Run all available garden fights.

CORE daily script - maximizes XP and ranking gains.

Usage:
    poetry run python scripts/run_fights.py        # Run all available fights
    poetry run python scripts/run_fights.py 10    # Run max 10 fights
    poetry run python scripts/run_fights.py -q    # Quiet mode
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.auth import login_api

LEEK_ID = 131321
HISTORY_FILE = Path(__file__).parent.parent / "data" / "fight_history.json"


def load_history() -> dict:
    """Load cumulative fight history."""
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"sessions": [], "total_fights": 0, "total_wins": 0, "total_losses": 0}


def save_history(history: dict):
    """Save fight history."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def main():
    # Parse args
    max_fights = 0  # 0 = all available
    quiet = False
    for arg in sys.argv[1:]:
        if arg == "-q" or arg == "--quiet":
            quiet = True
        elif arg.isdigit():
            max_fights = int(arg)

    api = login_api()

    farmer = api.farmer
    leeks = farmer["leeks"]
    leek_id = list(leeks.keys())[0]
    leek = leeks[leek_id]

    # Get garden state
    garden = api.get_garden()["garden"]
    available = garden.get("fights", 0)

    if available == 0:
        print("No fights available!")
        api.close()
        return

    to_fight = available if max_fights == 0 else min(max_fights, available)
    if not quiet:
        print(f"Running {to_fight} fights...\n")

    # Fight loop
    wins, losses, draws = 0, 0, 0
    fight_details = []

    for i in range(to_fight):
        try:
            opponents = api.get_leek_opponents(int(leek_id))["opponents"]
            if not opponents:
                print("No more opponents")
                break

            target = opponents[0]
            result = api.start_solo_fight(int(leek_id), target["id"])
            fight_id = result.get("fight")

            if not fight_id:
                print(f"[{i+1}] Failed: {result}")
                continue

            # Poll until fight completes (status=1 or report exists)
            fight = {}
            for _ in range(15):  # Max 15 attempts (30 seconds)
                time.sleep(2)
                fight_data = api.get_fight(fight_id)
                fight = fight_data if fight_data else {}
                if fight.get("report") is not None or fight.get("winner", -1) != -1:
                    break

            winner = fight.get("winner", 0)
            report = fight.get("report") or {}

            if winner == 1:
                wins += 1
                outcome = "W"
            elif winner == 2:
                losses += 1
                outcome = "L"
            else:
                draws += 1
                outcome = "D"

            if not quiet:
                print(f"[{i+1}/{to_fight}] {outcome} vs {target['name']} L{target['level']} ({report.get('duration', '?')}t)")

            fight_details.append({
                "id": fight_id,
                "opponent": target["name"],
                "opponent_level": target["level"],
                "result": outcome,
                "turns": report.get("duration", 0),
            })

        except Exception as e:
            print(f"[{i+1}] Error: {e}")
            time.sleep(2)

    # Summary
    total = wins + losses + draws
    win_rate = (wins / total * 100) if total > 0 else 0

    print(f"\n=== {wins}W-{losses}L-{draws}D ({win_rate:.0f}%) ===")

    # Check remaining and level
    garden = api.get_garden()["garden"]
    farmer = api.get_farmer(api.farmer_id)["farmer"]
    leek = farmer["leeks"][leek_id]
    print(f"Fights left: {garden.get('fights', 0)} | Level: {leek.get('level')} | XP: {leek.get('xp', 0)}/{leek.get('up_xp', 0)}")

    # Save history
    history = load_history()
    history["sessions"].append({
        "date": datetime.now().isoformat(),
        "fights": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "fight_details": fight_details,  # Save individual fight data
    })
    history["total_fights"] += total
    history["total_wins"] += wins
    history["total_losses"] += losses
    save_history(history)

    api.close()


if __name__ == "__main__":
    main()
