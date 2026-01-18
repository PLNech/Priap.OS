#!/usr/bin/env python3
"""Setup a proper mirror match with identical test leeks."""

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

    # Get test data
    response = api._client.get("/test-scenario/get-all", headers=api._headers())
    data = response.json()

    print("\n=== Current Test Leeks ===")
    for leek in data.get("leeks", []):
        print(f"  {leek['name']} (ID: {leek['id']})")
        print(f"    Level: {leek['level']}, Life: {leek['life']}")
        print(f"    STR: {leek['strength']}, AGI: {leek['agility']}, FREQ: {leek['frequency']}")
        print(f"    Weapons: {leek['weapons']}, Chips: {leek['chips']}")

    # Update all test leeks to have identical stats
    target_stats = {
        "level": 10,
        "life": 127,
        "strength": 100,
        "wisdom": 0,
        "agility": 0,
        "resistance": 0,
        "frequency": 100,
        "science": 0,
        "magic": 0,
        "tp": 10,
        "mp": 3,
        "cores": 1,
        "ram": 100,
    }

    print("\n=== Updating Test Leeks to Identical Stats ===")
    headers = api._headers()
    headers["Content-Type"] = "application/json"

    for leek in data.get("leeks", []):
        print(f"Updating {leek['name']}...", end=" ")
        time.sleep(1)
        # The API expects data to be JSON-stringified under "data" field
        update_data = {
            **target_stats,
            "weapons": [37],  # Pistol only
            "chips": [],
        }
        response = api._client.post(
            "/test-leek/update",
            headers=headers,
            json={
                "id": leek["id"],
                "data": json.dumps(update_data),
            }
        )
        if response.status_code == 200:
            print("OK")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    # Verify
    time.sleep(1)
    response = api._client.get("/test-scenario/get-all", headers=api._headers())
    data = response.json()

    print("\n=== Updated Test Leeks ===")
    for leek in data.get("leeks", []):
        print(f"  {leek['name']} (ID: {leek['id']})")
        print(f"    Level: {leek['level']}, Life: {leek['life']}")
        print(f"    STR: {leek['strength']}, AGI: {leek['agility']}, FREQ: {leek['frequency']}")

    api.close()


if __name__ == "__main__":
    main()
