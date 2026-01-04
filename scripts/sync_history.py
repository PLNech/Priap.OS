#!/usr/bin/env python3
"""Sync fight history from LeekWars API to local storage.

Usage:
    poetry run python scripts/sync_history.py           # Sync new fights
    poetry run python scripts/sync_history.py --full    # Full re-sync
    poetry run python scripts/sync_history.py --analyze # Analyze local history
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI

LEEK_ID = 131321
FARMER_ID = 124831
FIGHTS_DIR = Path(__file__).parent.parent / "data" / "fights"
INDEX_FILE = FIGHTS_DIR / "index.json"


def load_index() -> dict:
    """Load fight index."""
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text())
    return {"fights": {}, "last_sync": None}


def save_index(index: dict):
    """Save fight index."""
    FIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2))


def save_fight(fight_id: int, fight_data: dict):
    """Save individual fight data."""
    FIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    (FIGHTS_DIR / f"{fight_id}.json").write_text(json.dumps(fight_data, indent=2))


def sync_fights(api: LeekWarsAPI, full: bool = False) -> int:
    """Sync fights from API. Returns count of new fights."""
    index = load_index()
    known_ids = set(index["fights"].keys())
    new_count = 0

    # Get FULL fight history from history endpoint
    print("Fetching full fight history...")
    response = api._client.get(f"/history/get-farmer-history/{FARMER_ID}")
    response.raise_for_status()
    fights = response.json().get("fights", [])
    print(f"Found {len(fights)} fights in history")

    for fight in fights:
        fight_id = str(fight["id"])

        if fight_id in known_ids and not full:
            continue

        # Use result directly from history (no extra API call needed)
        result = {"win": "W", "defeat": "L", "draw": "D"}.get(fight.get("result"), "?")

        # Get opponent from leeks arrays
        leeks1 = fight.get("leeks1", [])
        leeks2 = fight.get("leeks2", [])
        our_team = 1 if any(l.get("id") == LEEK_ID for l in leeks1) else 2
        opp_leeks = leeks2 if our_team == 1 else leeks1
        opp_name = opp_leeks[0].get("name", "?") if opp_leeks else "?"

        index["fights"][fight_id] = {
            "date": fight.get("date", 0),
            "result": result,
            "opponent": opp_name,
            "context": fight.get("context", 0),
            "levelups": fight.get("levelups", 0),
            "trophies": fight.get("trophies", 0),
        }
        new_count += 1
        print(f"  {fight_id}: {result} vs {opp_name}")

    index["last_sync"] = datetime.now().isoformat()
    save_index(index)
    return new_count


def fetch_fight_details(api: LeekWarsAPI, fight_id: int) -> dict | None:
    """Fetch full fight data for detailed analysis."""
    try:
        fight = api.get_fight(fight_id)
        save_fight(fight_id, fight)
        return fight
    except Exception as e:
        print(f"Error fetching {fight_id}: {e}")
        return None


def analyze_history():
    """Analyze local fight history."""
    index = load_index()
    fights = index.get("fights", {})

    if not fights:
        print("No fights in local history. Run sync first.")
        return

    wins = sum(1 for f in fights.values() if f["result"] == "W")
    losses = sum(1 for f in fights.values() if f["result"] == "L")
    draws = sum(1 for f in fights.values() if f["result"] == "D")
    total = len(fights)

    print(f"\n{'='*60}")
    print("FIGHT HISTORY ANALYSIS")
    print(f"{'='*60}")
    print(f"Total: {total} | Record: {wins}W-{losses}L-{draws}D ({wins/total*100:.1f}%)")
    print()

    # Recent fights
    sorted_fights = sorted(fights.items(), key=lambda x: x[1].get("date", 0), reverse=True)
    print("Recent 20 fights:")
    for fight_id, f in sorted_fights[:20]:
        print(f"  {fight_id}: {f['result']} vs {f['opponent']}")

    # All losses
    losses_list = [(fid, f) for fid, f in sorted_fights if f["result"] == "L"]
    print(f"\nAll losses ({len(losses_list)}):")
    for fight_id, f in losses_list:
        print(f"  {fight_id}: vs {f['opponent']}")

    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Sync and analyze fight history")
    parser.add_argument("--full", action="store_true", help="Full re-sync")
    parser.add_argument("--analyze", action="store_true", help="Analyze only")
    parser.add_argument("--fetch", type=int, help="Fetch full details for fight ID")

    args = parser.parse_args()

    if args.analyze:
        analyze_history()
        return

    api = LeekWarsAPI()
    api.login("leek@nech.pl", "REDACTED_PASSWORD")

    if args.fetch:
        print(f"Fetching fight {args.fetch}...")
        fight = fetch_fight_details(api, args.fetch)
        if fight:
            print(f"Saved to data/fights/{args.fetch}.json")
    else:
        new_count = sync_fights(api, full=args.full)
        print(f"\nSynced {new_count} fights")
        analyze_history()

    api.close()


if __name__ == "__main__":
    main()
