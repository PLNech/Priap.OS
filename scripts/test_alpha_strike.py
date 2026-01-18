#!/usr/bin/env python3
"""Upload alpha_strike AI and run 25 test fights."""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api

LEEK_ID = 131321

def main():
    n_fights = int(sys.argv[1]) if len(sys.argv) > 1 else 25

    api = login_api()
    print(f"Logged in as farmer {api.farmer_id}")

    # Get AI ID
    ais = api.get_farmer_ais().get("ais", [])
    ai_id = ais[0]["id"] if ais else None
    print(f"AI ID: {ai_id}, Name: {ais[0]['name'] if ais else 'N/A'}")

    # Read and upload alpha_strike code
    code = Path("ais/alpha_strike.leek").read_text()
    print(f"\nUploading alpha_strike AI ({len(code)} chars)...")
    result = api.save_ai(ai_id, code)

    if result.get("result") == "error":
        print(f"Upload failed: {result}")
        api.close()
        return
    print("Upload OK")

    # Get garden state
    garden = api.get_garden()["garden"]
    available = garden.get("fights", 0)
    print(f"\nFights available: {available}")

    to_fight = min(n_fights, available)
    print(f"Running {to_fight} fights with alpha_strike...\n")

    # Fight loop
    wins, losses, draws = 0, 0, 0

    for i in range(to_fight):
        try:
            opponents = api.get_leek_opponents(LEEK_ID)["opponents"]
            if not opponents:
                print("No more opponents")
                break

            target = opponents[0]
            result = api.start_solo_fight(LEEK_ID, target["id"])
            fight_id = result.get("fight")

            if not fight_id:
                print(f"[{i+1}] Failed: {result}")
                continue

            time.sleep(1.5)
            fight = api.get_fight(fight_id)
            winner = fight.get("winner")
            report = fight.get("report", {})

            if winner == 1:
                wins += 1
                outcome = "W"
            elif winner == 2:
                losses += 1
                outcome = "L"
            else:
                draws += 1
                outcome = "D"

            print(f"[{i+1}/{to_fight}] {outcome} vs {target['name']} L{target['level']} ({report.get('duration', '?')}t)")

        except Exception as e:
            print(f"[{i+1}] Error: {e}")
            time.sleep(2)

    # Summary
    total = wins + losses + draws
    win_rate = (wins / total * 100) if total > 0 else 0
    decisive = wins + losses
    win_rate_decisive = (wins / decisive * 100) if decisive > 0 else 0

    print(f"\n{'='*50}")
    print(f"ALPHA STRIKE RESULTS: {wins}W-{losses}L-{draws}D")
    print(f"Win rate: {win_rate:.1f}% (all) / {win_rate_decisive:.1f}% (decisive)")
    print(f"{'='*50}")
    print(f"\nBaseline v1: 56.5% (52W/40L)")
    diff = win_rate_decisive - 56.5
    print(f"Difference: {diff:+.1f}%")
    if diff > 5:
        print(">>> POSITIVE signal - alpha strike is better!")
    elif diff < -5:
        print(">>> NEGATIVE signal - v1 is better")
    else:
        print(">>> NEUTRAL - no clear winner yet")

    api.close()


if __name__ == "__main__":
    main()
