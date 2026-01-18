#!/usr/bin/env python3
"""Scrape fight history from LeekWars website.

Usage:
    poetry run python scripts/parse_history.py 131321
    poetry run python scripts/parse_history.py 131321 --fetch-all
"""

import sys
import os
import argparse
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api


def parse_history_page(leek_id: int, fetch_fights: bool = False) -> dict:
    """
    Scrape fight history for a leek.

    Note: There's no bulk fight history API endpoint, so we'll need to either:
    1. Track fight IDs locally as we run them (preferred)
    2. Scrape the HTML history page (complex, fragile)
    3. Use the fights we already saved in data/

    For now, we'll use approach #3 - read from local fight data.
    """

    api = login_api()

    # Get leek info
    leek_data = api.get_leek(leek_id)
    print(f"Leek: {leek_data['leek']['name']} (Level {leek_data['leek']['level']})")

    # Check for locally saved fight data
    fights_dir = Path(__file__).parent.parent / "data" / "fights"
    if not fights_dir.exists():
        print("No local fight data found.")
        print("Run fights with run_fights.py first, or use fetch_fight.py to download specific fights.")
        return {"leek_id": leek_id, "fights": []}

    # Read all saved fights
    fight_files = sorted(fights_dir.glob("fight_*.json"))
    print(f"Found {len(fight_files)} saved fights\n")

    fights = []
    for fight_file in fight_files:
        fight_data = json.loads(fight_file.read_text())

        # Extract basic info
        fight_id = fight_data.get("id")
        winner = fight_data.get("winner")

        # Check if our leek was in this fight
        leeks = fight_data.get("data", {}).get("leeks", [])
        our_leek = None
        opponent_leek = None

        for leek in leeks:
            # Match by entity ID or name
            if leek.get("name") == leek_data["leek"]["name"]:
                our_leek = leek
            else:
                opponent_leek = leek

        if our_leek:
            our_team = our_leek.get("team")
            result = "W" if winner == our_team else "L" if winner else "D"

            fight_info = {
                "id": fight_id,
                "result": result,
                "opponent": opponent_leek.get("name") if opponent_leek else "Unknown",
                "opponent_level": opponent_leek.get("level") if opponent_leek else 0,
                "file": str(fight_file),
            }
            fights.append(fight_info)

            print(f"Fight {fight_id}: {result} vs {fight_info['opponent']} (L{fight_info['opponent_level']})")

    api.close()

    # Summary
    wins = sum(1 for f in fights if f["result"] == "W")
    losses = sum(1 for f in fights if f["result"] == "L")
    print(f"\nSummary: {wins}W-{losses}L ({wins/(wins+losses)*100:.1f}% win rate)" if fights else "No fights found")

    return {
        "leek_id": leek_id,
        "total_fights": len(fights),
        "wins": wins,
        "losses": losses,
        "fights": fights,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse fight history for a leek")
    parser.add_argument("leek_id", type=int, help="Leek ID")
    parser.add_argument("--fetch-all", action="store_true", help="Fetch full data for all fights")

    args = parser.parse_args()

    history = parse_history_page(args.leek_id, fetch_fights=args.fetch_all)

    # Save summary
    output_file = Path(__file__).parent.parent / "data" / f"history_{args.leek_id}.json"
    output_file.write_text(json.dumps(history, indent=2))
    print(f"\nSaved summary to {output_file}")


if __name__ == "__main__":
    main()
