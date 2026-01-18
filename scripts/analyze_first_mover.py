#!/usr/bin/env python3
"""Analyze first-mover advantage from real garden fights.

Goal: Determine if we have first-mover advantage by correlating
'starter' (who attacked) with fight outcomes.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api

MY_FARMER_ID = 124831
MY_LEEK_ID = 131321


def analyze_fights():
    # Load fight index
    with open("data/fights/index.json") as f:
        index = json.load(f)

    fights = index.get("fights", {})
    print(f"Total fights in index: {len(fights)}")

    # Filter to garden fights (context=2) with decisive results
    garden_fights = {
        fid: info for fid, info in fights.items()
        if info.get("context") == 2 and info.get("result") in ("W", "L")
    }
    print(f"Garden fights with W/L results: {len(garden_fights)}")

    # Connect to API to fetch fight details
    api = login_api()
    print(f"Logged in as farmer {api.farmer_id}")

    results = []

    # Sample fights (fetch details to get starter)
    fight_ids = list(garden_fights.keys())
    n_sample = min(50, len(fight_ids))

    print(f"\nFetching {n_sample} fight details...")
    for i, fid in enumerate(fight_ids[:n_sample]):
        print(f"  {i+1}/{n_sample}: Fight {fid}...", end=" ", flush=True)

        try:
            fight = api.get_fight(int(fid))

            starter = fight.get("starter")  # Who attacked (farmer ID)
            winner = fight.get("winner")    # 1 = leeks1 wins, 2 = leeks2 wins

            # Determine which team we're on
            leeks1 = fight.get("leeks1", [])
            leeks2 = fight.get("leeks2", [])

            our_team = None
            if any(l.get("id") == MY_LEEK_ID for l in leeks1):
                our_team = 1
            elif any(l.get("id") == MY_LEEK_ID for l in leeks2):
                our_team = 2

            # Determine who started
            we_started = (starter == MY_FARMER_ID)
            we_won = (winner == our_team)

            result = {
                "fight_id": int(fid),
                "starter": starter,
                "winner": winner,
                "our_team": our_team,
                "we_started": we_started,
                "we_won": we_won,
            }
            results.append(result)

            status = "W" if we_won else "L"
            first = "ATTACK" if we_started else "DEFEND"
            print(f"{status} ({first})")

            time.sleep(0.5)  # Rate limit

        except Exception as e:
            print(f"Error: {e}")
            continue

    api.close()

    # Analyze
    print("\n" + "="*60)
    print("FIRST-MOVER ADVANTAGE ANALYSIS")
    print("="*60)

    # Overall stats
    wins = sum(1 for r in results if r["we_won"])
    losses = len(results) - wins
    print(f"\nOverall: {wins}W / {losses}L ({100*wins/len(results):.1f}% win rate)")

    # When we attack (we started)
    attack_fights = [r for r in results if r["we_started"]]
    attack_wins = sum(1 for r in attack_fights if r["we_won"])
    if attack_fights:
        print(f"\nWhen we ATTACK (we start): {attack_wins}W / {len(attack_fights)-attack_wins}L ({100*attack_wins/len(attack_fights):.1f}%)")

    # When we defend (they started)
    defend_fights = [r for r in results if not r["we_started"]]
    defend_wins = sum(1 for r in defend_fights if r["we_won"])
    if defend_fights:
        print(f"When we DEFEND (they start): {defend_wins}W / {len(defend_fights)-defend_wins}L ({100*defend_wins/len(defend_fights):.1f}%)")

    # First-mover advantage calculation
    if attack_fights and defend_fights:
        attack_rate = attack_wins / len(attack_fights)
        defend_rate = defend_wins / len(defend_fights)
        advantage = attack_rate - defend_rate
        print(f"\n** FIRST-MOVER ADVANTAGE: {advantage*100:+.1f}% **")

        if advantage > 0.1:
            print("   -> SIGNIFICANT: Attacking first helps!")
        elif advantage < -0.1:
            print("   -> SIGNIFICANT: Defending is better!")
        else:
            print("   -> NEUTRAL: Initiative doesn't matter much")

    # Save results
    with open("data/first_mover_analysis.json", "w") as f:
        json.dump({
            "results": results,
            "summary": {
                "total": len(results),
                "wins": wins,
                "attack_fights": len(attack_fights),
                "attack_wins": attack_wins,
                "defend_fights": len(defend_fights),
                "defend_wins": defend_wins,
            }
        }, f, indent=2)
    print("\nResults saved to data/first_mover_analysis.json")


if __name__ == "__main__":
    analyze_fights()
