#!/usr/bin/env python3
"""Fetch recent fight IDs from LeekWars garden history."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api

def main():
    api = login_api()

    # Get garden with recent fights
    garden = api.get_garden()

    if "garden" in garden and "fights" in garden["garden"]:
        fights = garden["garden"]["fights"]
        print(f"Found {len(fights)} recent fights:\n")

        for fight in fights[:15]:  # Show last 15
            fight_data = fight.get("fight", {})
            fight_id = fight_data.get("id")
            winner = fight_data.get("winner")
            type_val = fight_data.get("type")

            # Figure out outcome
            if type_val == 0:  # Solo fight
                team1 = fight_data.get("team1", [])
                team2 = fight_data.get("team2", [])
                if team1 and team2:
                    us = team1[0]
                    them = team2[0]
                    outcome = "W" if winner == 1 else "L" if winner == 2 else "D"
                    print(f"[{outcome}] Fight {fight_id} vs {them.get('name', '?')}")
            else:
                print(f"[?] Fight {fight_id} (type {type_val})")
    else:
        print("No fights found in garden")

    api.close()

if __name__ == "__main__":
    main()
