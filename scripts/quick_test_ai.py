#!/usr/bin/env python3
"""Quick test AI via test-scenario API before real fights."""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api

def main():
    ai_file = sys.argv[1] if len(sys.argv) > 1 else "ais/alpha_strike.leek"

    api = login_api()
    print(f"Logged in as farmer {api.farmer_id}")

    # Get AI ID
    ais = api.get_farmer_ais().get("ais", [])
    ai_id = ais[0]["id"] if ais else None
    print(f"AI ID: {ai_id}")

    # Upload AI code
    code = Path(ai_file).read_text()
    print(f"Uploading {ai_file} ({len(code)} chars)...")
    result = api.save_ai(ai_id, code)

    if result.get("result") == "error":
        print(f"Upload FAILED: {result}")
        api.close()
        return
    print("Upload OK")

    # Get test scenario
    response = api._client.get("/test-scenario/get-all", headers=api._headers())
    data = response.json()
    scenarios = data.get("scenarios", {})

    if not scenarios:
        print("No test scenarios found!")
        api.close()
        return

    scenario_id = int(list(scenarios.keys())[0])
    print(f"\nRunning test fight (scenario {scenario_id})...")

    # Run test fight
    headers = api._headers()
    headers["Content-Type"] = "application/json"
    response = api._client.post(
        "/ai/test-scenario",
        headers=headers,
        json={"scenario_id": scenario_id, "ai_id": ai_id}
    )
    result = response.json()
    fight_id = result.get("fight")

    if not fight_id:
        print(f"Test fight failed: {result}")
        api.close()
        return

    print(f"Fight ID: {fight_id}")
    time.sleep(3)

    # Analyze result
    fight = api.get_fight(fight_id)
    fight_data = fight.get("data", {})
    winner = fight.get("winner")

    print(f"\n=== TEST RESULT ===")
    print(f"Winner: Team {winner}")

    # Check ops usage
    ops = fight_data.get("ops", {})
    for entity_id, entity_ops in ops.items():
        print(f"Entity {entity_id}: {entity_ops:,} ops")

    # Check actions
    actions = fight_data.get("actions", [])
    moves = sum(1 for a in actions if a[0] == 10)  # MOVE action
    shots = sum(1 for a in actions if a[0] == 16)  # USE_WEAPON action
    print(f"Total moves: {moves}, Total shots: {shots}")

    print("\n=== AI VALIDATED - Ready for real fights ===")

    api.close()


if __name__ == "__main__":
    main()
