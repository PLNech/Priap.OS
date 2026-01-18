#!/usr/bin/env python3
"""Recreate test scenario with proper AI assignment."""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api


def main():
    api = login_api()
    print(f"Logged in as farmer {api.farmer_id}")

    headers = api._headers()
    headers["Content-Type"] = "application/json"

    # Get current data
    response = api._client.get("/test-scenario/get-all", headers=api._headers())
    data = response.json()

    # Delete existing scenarios
    for sid in data.get("scenarios", {}).keys():
        print(f"Deleting scenario {sid}...")
        time.sleep(0.5)
        api._client.delete(f"/test-scenario/delete/{sid}", headers=headers)

    # Get AI ID
    ais = api.get_farmer_ais().get("ais", [])
    ai_id = ais[0]["id"] if ais else None
    print(f"Using AI: {ai_id}")

    # Get test leeks
    response = api._client.get("/test-scenario/get-all", headers=api._headers())
    data = response.json()
    test_leeks = data.get("leeks", [])
    print(f"Test leeks: {[l['name'] for l in test_leeks]}")

    if len(test_leeks) < 2:
        print("Need at least 2 test leeks!")
        return

    # Create new scenario
    print("\nCreating new scenario...")
    time.sleep(1)
    response = api._client.post(
        "/test-scenario/new",
        headers=headers,
        json={"name": "TrueMirror"}
    )
    scenario = response.json()
    print(f"Created: {scenario}")
    scenario_id = scenario.get("id")

    # Add leeks with EXPLICIT AI
    time.sleep(1)
    print(f"\nAdding {test_leeks[0]['name']} to team1 with AI {ai_id}...")
    response = api._client.post(
        "/test-scenario/add-leek",
        headers=headers,
        json={
            "scenario_id": scenario_id,
            "leek": test_leeks[0]["id"],
            "team": 0,  # Team 1
            "ai": ai_id,
        }
    )
    print(f"Response: {response.json()}")

    time.sleep(1)
    print(f"\nAdding {test_leeks[1]['name']} to team2 with AI {ai_id}...")
    response = api._client.post(
        "/test-scenario/add-leek",
        headers=headers,
        json={
            "scenario_id": scenario_id,
            "leek": test_leeks[1]["id"],
            "team": 1,  # Team 2
            "ai": ai_id,
        }
    )
    print(f"Response: {response.json()}")

    # Verify
    time.sleep(1)
    response = api._client.get("/test-scenario/get-all", headers=api._headers())
    data = response.json()
    print("\n=== Final Scenario ===")
    print(json.dumps(data.get("scenarios", {}), indent=2))

    # Run a test fight
    time.sleep(1)
    print("\n=== Running Test Fight ===")
    response = api._client.post(
        "/ai/test-scenario",
        headers=headers,
        json={
            "scenario_id": scenario_id,
            "ai_id": ai_id,
        }
    )
    result = response.json()
    fight_id = result.get("fight")
    print(f"Fight ID: {fight_id}")

    # Wait and analyze
    time.sleep(3)
    fight = api.get_fight(fight_id)
    fight_data = fight.get("data", {})

    print(f"\nWinner: Team {fight.get('winner')}")
    print(f"Ops: {fight_data.get('ops', {})}")

    # Check actions for Entity 1
    actions = fight_data.get("actions", [])
    e1_actions = [a for a in actions if a[0] in (10, 13, 16) and len(a) > 1 and a[1] == 1]
    print(f"\nEntity 1 actions (move/weapon/use): {len(e1_actions)}")
    for a in e1_actions[:5]:
        print(f"  {a}")

    api.close()


if __name__ == "__main__":
    main()
