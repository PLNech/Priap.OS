#!/usr/bin/env python3
"""Fetch and save fight data by ID.

Usage:
    poetry run python scripts/fetch_fight.py 50863105
    poetry run python scripts/fetch_fight.py 50863105 --analyze
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.fight_parser import parse_fight


def fetch_fight(fight_id: int, save: bool = True, analyze: bool = False) -> dict:
    """Fetch fight data from API."""
    api = LeekWarsAPI()

    print(f"Fetching fight {fight_id}...")
    fight_data = api.get_fight(fight_id)

    if save:
        output_dir = Path(__file__).parent.parent / "data" / "fights"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"fight_{fight_id}.json"
        output_file.write_text(json.dumps(fight_data, indent=2))
        print(f"Saved to {output_file}")

    if analyze:
        print("\n=== Fight Analysis ===")
        parsed = parse_fight(fight_data)

        # Basic info
        winner = parsed.get("winner")
        turns = parsed.get("summary", {}).get("turns", 0)
        print(f"Winner: Team {winner}")
        print(f"Turns: {turns}")

        # Damage breakdown
        damage = parsed.get("summary", {}).get("damage_dealt", {})
        for entity_id, dmg in damage.items():
            print(f"Entity {entity_id}: {dmg} damage dealt")

        # Shots fired
        weapon_uses = parsed.get("summary", {}).get("weapon_uses", 0)
        print(f"Total weapon uses: {weapon_uses}")

    api.close()
    return fight_data


def main():
    if len(sys.argv) < 2:
        print("Usage: poetry run python scripts/fetch_fight.py <fight_id> [--analyze]")
        sys.exit(1)

    fight_id = int(sys.argv[1])
    analyze = "--analyze" in sys.argv

    fetch_fight(fight_id, save=True, analyze=analyze)


if __name__ == "__main__":
    main()
