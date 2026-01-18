#!/usr/bin/env python3
"""Test fighting via API."""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import httpx
from leekwars_agent.auth import get_credentials

USERNAME, PASSWORD = get_credentials()
BASE = "https://leekwars.com/api"

client = httpx.Client(timeout=30.0)

# Login
print("=== LOGIN ===")
r = client.post(
    f"{BASE}/farmer/login",
    data={"login": USERNAME, "password": PASSWORD, "keep_connected": "true"},
)
data = r.json()
farmer = data["farmer"]
token = None
for cookie in r.cookies.jar:
    if cookie.name == "token":
        token = cookie.value
        break

headers = {"Authorization": f"Bearer {token}"}
print(f"Logged in as: {farmer['name']}")
print(f"Token: {token[:50]}...")

# Get leek info
leeks = farmer["leeks"]
leek_id = list(leeks.keys())[0]
leek = leeks[leek_id]
print(f"\nLeek: {leek['name']} (ID: {leek_id})")

# Check garden
print("\n=== GARDEN STATE ===")
r = client.get(f"{BASE}/garden/get", headers=headers)
garden = r.json().get("garden", {})
print(f"Leeks in garden: {garden.get('leeks', [])}")
print(f"Solo fights available: {len(garden.get('solo_fights', []))}")

# Try to set leek in garden
print("\n=== SETTING LEEK IN GARDEN ===")
# Endpoint: leek/set-in-garden
r = client.post(
    f"{BASE}/leek/set-in-garden",
    headers=headers,
    data={"leek_id": leek_id, "in_garden": "true"},
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

# Check garden again
print("\n=== GARDEN STATE (after) ===")
r = client.get(f"{BASE}/garden/get", headers=headers)
garden = r.json().get("garden", {})
print(f"Leeks in garden: {garden.get('leeks', [])}")

# Get opponents
print("\n=== OPPONENTS ===")
r = client.get(f"{BASE}/garden/get-leek-opponents/{leek_id}", headers=headers)
opps = r.json().get("opponents", [])
print(f"Found {len(opps)} opponents")
for opp in opps[:5]:
    print(f"  - {opp.get('name')} L{opp.get('level')} T{opp.get('talent')} (ID: {opp.get('id')})")

# Try starting a fight
if opps and "--fight" in sys.argv:
    target = opps[0]
    print(f"\n=== STARTING FIGHT vs {target['name']} ===")
    r = client.post(
        f"{BASE}/garden/start-solo-fight",
        headers=headers,
        data={"leek_id": leek_id, "target_id": target["id"]},
    )
    print(f"Status: {r.status_code}")
    result = r.json()
    print(f"Response keys: {list(result.keys())}")

    if "fight" in result:
        fight_id = result["fight"]
        print(f"Fight ID: {fight_id}")

        # Wait for fight to complete
        print("Waiting for fight to complete...")
        time.sleep(3)

        # Get fight result
        r = client.get(f"{BASE}/fight/get/{fight_id}")
        fight = r.json()
        print(f"\nFight keys: {list(fight.keys())}")
        if "fight" in fight:
            f = fight["fight"]
            print(f"Winner: {f.get('winner')}")
            print(f"Status: {f.get('status')}")
    else:
        print(f"Full response: {json.dumps(result, indent=2)[:500]}")
else:
    print("\n[INFO] Run with --fight to start a fight")

client.close()
